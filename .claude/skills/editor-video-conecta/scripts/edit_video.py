#!/usr/bin/env python3
"""Editor de vídeo por linha de comando: corte de silêncio + legendas animadas + títulos + gráficos.

Pipeline: transcreve (Whisper) -> corta silêncios -> legendas/overlays -> render final.
Todos os tempos dos overlays (start/duration) são na linha do tempo FINAL, já com os silêncios cortados.

Uso:
  python edit_video.py entrada.mp4 -o saida.mp4 --spec edicao.json
  python edit_video.py entrada.mp4 -o saida.mp4 --silence --subtitles viral
  python edit_video.py entrada.mp4 -o rascunho.mp4 --spec edicao.json --draft      # rápido, baixa resolução

Formato do spec (todas as chaves são opcionais): veja references/spec.md
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from build_ass import build_ass
from charts import render_chart
import shutil
from common import FONTS_DIR, load_json, probe, punch_schedule, require_ffmpeg, run, save_json
from cut_silence import process as cut_process
from transcribe import transcribe

TEXT_TYPES = ("title", "lower_third", "numbered_title")          # desenhados pelo .ass
VISUAL_TYPES = ("chart", "stat", "steps", "cards", "pillars")    # sequências PNG sobrepostas
PRESET_DIR = Path(__file__).resolve().parent.parent / "presets"

POSITIONS = {  # expressões do filtro overlay (W,H = quadro; w,h = gráfico)
    "full": "0:0", "top": "(W-w)/2:H*0.07", "center": "(W-w)/2:(H-h)/2", "bottom": "(W-w)/2:H*0.62",
    "top-left": "W*0.04:H*0.07", "top-right": "W-w-W*0.04:H*0.07",
    "bottom-left": "W*0.04:H-h-H*0.10", "bottom-right": "W-w-W*0.04:H-h-H*0.10",
}


def deep_merge(base, extra):
    out = dict(base)
    for k, v in extra.items():
        out[k] = deep_merge(out[k], v) if isinstance(v, dict) and isinstance(out.get(k), dict) else v
    return out


def punch_in_filter(W, H, duration, joins, cfg):
    """Zoom alternado a cada corte (efeito 'jump cut' de talking head) para o motor ffmpeg."""
    terms = [f"{z - 1:.3f}*between(t,{a:.3f},{b:.3f})" for a, b, z in punch_schedule(duration, joins, cfg) if z > 1.001]
    if not terms:
        return None
    z = "(1+" + "+".join(terms) + ")"
    return (f"scale=w='trunc({W}*{z}/2)*2':h='trunc({H}*{z}/2)*2':eval=frame,"
            f"crop={W}:{H}:(iw-{W})/2:(ih-{H})*0.3")


def apply_replacements(words, repl):
    if not repl:
        return words
    low = {k.lower(): v for k, v in repl.items()}
    out = []
    for w in words:
        core = w["word"].strip(".,!?;:")
        new = low.get(core.lower())
        out.append({**w, "word": w["word"].replace(core, new) if new else w["word"]})
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input")
    ap.add_argument("-o", "--output", required=True)
    ap.add_argument("--spec", help="JSON com a edição (silêncio, legendas, overlays)")
    ap.add_argument("--preset", default=None, help="preset de estilo em presets/<nome>.json (ex.: padrao)")
    ap.add_argument("--silence", action="store_true", help="liga o corte de silêncio")
    ap.add_argument("--subtitles", choices=["ref", "viral", "clean", "box"], help="liga legendas neste estilo")
    ap.add_argument("--transcript", help="usa este transcript.json em vez de transcrever")
    ap.add_argument("--workdir", help="pasta de trabalho (cache de transcript, quadros dos gráficos)")
    ap.add_argument("--model", default="small", help="modelo Whisper: tiny/base/small/medium/large-v3")
    ap.add_argument("--language", default="pt")
    ap.add_argument("--draft", action="store_true", help="renderiza rápido e em qualidade menor para conferir")
    ap.add_argument("--engine", choices=["hyperframes", "ffmpeg"], default="hyperframes",
                    help="motor dos overlays: hyperframes (HTML+GSAP, padrão) ou ffmpeg (ASS+matplotlib, sem Chrome/Node)")
    args = ap.parse_args()

    require_ffmpeg()
    spec = load_json(args.spec) if args.spec else {}
    preset_name = args.preset or spec.get("preset")
    if preset_name:
        spec = deep_merge(load_json(PRESET_DIR / f"{preset_name}.json"), spec)
    if args.silence:
        spec.setdefault("silence", {})["enabled"] = True
    if args.subtitles:
        spec.setdefault("subtitles", {})["style"] = args.subtitles
        spec["subtitles"]["enabled"] = True

    src, out = Path(args.input).resolve(), Path(args.output).resolve()
    work = Path(args.workdir).resolve() if args.workdir else out.parent / (out.stem + "_work")
    work.mkdir(parents=True, exist_ok=True)
    sil, sub = spec.get("silence", {}), spec.get("subtitles", {})
    want_sil, want_sub = sil.get("enabled", False), sub.get("enabled", False)

    # 1) transcript (precisa para legendas; também permite remapear tempos após o corte)
    words = None
    if want_sub:
        tpath = Path(args.transcript) if args.transcript else work / "transcript.json"
        if tpath.exists():
            words = load_json(tpath)["words"]
        else:
            print("Transcrevendo com Whisper (a 1ª vez baixa o modelo)...")
            data = transcribe(src, args.model, spec.get("language", args.language), spec.get("prompt"))
            save_json(data, tpath)
            words = data["words"]
        words = apply_replacements(words, spec.get("replacements"))

    # 2) corte de silêncio
    current, stats = src, None
    if want_sil:
        current = work / "cut.mp4"
        words, stats = cut_process(src, current, words, sil.get("threshold_db", -32.0),
                                   sil.get("min_silence", 0.45), sil.get("padding", 0.10))
        print("Corte de silêncio:", {k: v for k, v in stats.items() if k != "joins"})

    # 3a) motor HyperFrames: composição HTML/GSAP renderizada por Chrome headless + FFmpeg
    if args.engine == "hyperframes":
        from hf_project import build_project, render
        if current == src:                       # sem corte: normaliza GOP/fps para o HyperFrames buscar quadros rápido
            current = work / "base_prep.mp4"
            run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(src), "-r", "30", "-c:v", "libx264",
                 "-preset", "veryfast", "-crf", "16", "-g", "30", "-keyint_min", "30", "-pix_fmt", "yuv420p",
                 "-c:a", "aac", "-b:a", "192k", str(current)])
        build_project(work / "hf", current, words, {**spec, "subtitles": {**sub, "enabled": want_sub}}, (stats or {}).get("joins", []))
        print("Renderizando com HyperFrames...")
        try:
            render(work / "hf", out, draft=args.draft)
        except RuntimeError as e:
            sys.exit(f"{e}\n\nDica: sem Node 22+/Chrome, use --engine ffmpeg.")
        print(f"Pronto: {out}")
        if stats:
            print(f"Silêncio removido: {stats['removed_s']}s ({stats['original_s']}s -> {stats['final_s']}s)")
        return

    # 3b) motor FFmpeg: legendas + overlays de texto via ASS
    info = probe(current)
    W, H = info["width"], info["height"]
    overlays = spec.get("overlays", [])
    theme = spec.get("theme", {})
    ass_path = work / "edit.ass"
    ass_path.write_text(build_ass(words, W, H, {**sub, "enabled": want_sub}, overlays, theme, spec.get("font")),
                        encoding="utf-8")

    # 4) gráficos animados
    chart_inputs, graph, last = [], [], "[0:v]"
    punch = spec.get("punch_in", {})
    if punch.get("enabled"):
        pf = punch_in_filter(W, H, info["duration"], (stats or {}).get("joins", []), punch)
        if pf:
            graph.append(f"[0:v]{pf}[zv]")
            last = "[zv]"
    for i, ov in enumerate([o for o in overlays if o.get("type") in VISUAL_TYPES]):
        cspec = {**ov, "kind": ov["type"] if ov["type"] != "chart" else ov.get("kind", "bar")}
        meta = render_chart(cspec, W, H, work / f"chart_{i}", theme, font=spec.get("font"))
        chart_inputs += ["-framerate", str(meta["fps"]), "-i", f"{meta['dir']}/%04d.png"]
        s, d = ov["start"], ov["duration"]
        hold = max(0.0, d - meta["anim"])
        lab, out_lab = f"[c{i}]", f"[o{i}]"
        graph.append(f"[{i + 1}:v]format=rgba,tpad=stop_mode=clone:stop_duration={hold:.3f},"
                     f"fade=t=in:st=0:d=0.2:alpha=1,fade=t=out:st={max(d - 0.3, 0):.3f}:d=0.3:alpha=1,"
                     f"setpts=PTS-STARTPTS+{s:.3f}/TB{lab}")
        pos = POSITIONS.get(ov.get("position", "top"), POSITIONS["top"])
        graph.append(f"{last}{lab}overlay={pos}:enable='between(t,{s:.3f},{s + d:.3f})':eof_action=pass{out_lab}")
        last = out_lab

    # copia as fontes da marca para a pasta de trabalho: libass as encontra via fontsdir (caminho relativo, sem escape)
    fonts_work = work / "fonts"
    fonts_work.mkdir(exist_ok=True)
    for f in (FONTS_DIR.iterdir() if FONTS_DIR.exists() else []):
        if f.suffix.lower() in (".ttf", ".otf"):
            shutil.copy2(f, fonts_work / f.name)
    post = f"ass={ass_path.name}:fontsdir=fonts"
    if args.draft:
        post = f"scale=-2:540,{post}" if H >= W else f"scale=960:-2,{post}"
        # no rascunho a escala é aplicada ANTES das legendas, então precisamos de um .ass nas dimensões novas
        dw, dh = (round(W * 540 / H / 2) * 2, 540) if H >= W else (960, round(H * 960 / W / 2) * 2)
        (work / "edit_draft.ass").write_text(build_ass(words, dw, dh, {**sub, "enabled": want_sub},
                                                      [o for o in overlays if o.get("type") in TEXT_TYPES],
                                                      theme, spec.get("font")), encoding="utf-8")
        post = f"scale={dw}:{dh},ass=edit_draft.ass:fontsdir=fonts"
    graph.append(f"{last}{post}[v]")

    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(current), *chart_inputs,
           "-filter_complex", ";".join(graph), "-map", "[v]"]
    if info["has_audio"]:
        cmd += ["-map", "0:a", "-c:a", "aac", "-b:a", "192k"]
    cmd += ["-c:v", "libx264", "-preset", "veryfast", "-crf", "28" if args.draft else "20",
            "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(out)]
    print("Renderizando...")
    run(cmd, cwd=work)
    print(f"Pronto: {out}")
    if stats:
        print(f"Silêncio removido: {stats['removed_s']}s ({stats['original_s']}s -> {stats['final_s']}s)")


if __name__ == "__main__":
    main()
