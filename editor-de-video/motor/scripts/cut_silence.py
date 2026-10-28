#!/usr/bin/env python3
"""Remove silêncios de um vídeo e (opcionalmente) remapeia o transcript para a nova linha do tempo.

Uso:
  python cut_silence.py in.mp4 -o out.mp4 [--threshold -32] [--min-silence 0.45] [--padding 0.10]
         [--transcript t.json --out-transcript t_cut.json]
"""
import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import load_json, probe, require_ffmpeg, run, save_json


def detect_silences(path, threshold_db=-32.0, min_silence=0.45):
    """Lista de (início, fim) dos silêncios detectados pelo filtro silencedetect."""
    res = run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-vn",
               "-af", f"silencedetect=noise={threshold_db}dB:d={min_silence}",
               "-f", "null", "-"], capture=True)
    duration = probe(path)["duration"]
    silences, start = [], None
    for line in res.stderr.splitlines():
        m = re.search(r"silence_start: (-?[\d.]+)", line)
        if m:
            start = max(0.0, float(m.group(1)))
            continue
        m = re.search(r"silence_end: ([\d.]+)", line)
        if m and start is not None:
            silences.append((start, float(m.group(1))))
            start = None
    if start is not None:                    # silêncio que vai até o fim do arquivo
        silences.append((start, duration))
    return silences, duration


def keep_segments(silences, duration, padding=0.10, min_cut=0.15):
    """Inverte os silêncios em trechos a manter, deixando 'padding' de respiro em cada borda da fala."""
    cuts = []
    for s, e in silences:
        cs = s + padding if s > 0.01 else s          # no início do vídeo não há fala para proteger
        ce = e - padding if e < duration - 0.01 else e
        if ce - cs >= min_cut:
            cuts.append((cs, ce))
    keeps, cursor = [], 0.0
    for cs, ce in cuts:
        if cs - cursor > 0.05:
            keeps.append((cursor, cs))
        cursor = ce
    if duration - cursor > 0.05:
        keeps.append((cursor, duration))
    return keeps or [(0.0, duration)]


def remap_words(words, keeps):
    """Converte tempos da linha do tempo original para a linha do tempo já cortada."""
    offsets, acc = [], 0.0
    for a, b in keeps:
        offsets.append(acc)
        acc += b - a
    out = []
    for w in words:
        mid = (w["start"] + w["end"]) / 2
        for (a, b), off in zip(keeps, offsets):
            if a - 1e-3 <= mid <= b + 1e-3:
                s = max(w["start"], a) - a + off
                e = min(w["end"], b) - a + off
                out.append({**w, "start": round(s, 3), "end": round(max(e, s + 0.05), 3)})
                break                         # palavra dentro de trecho cortado é descartada
    return out


def render_cut(src, dst, keeps, has_audio=True, crf=18, workdir=None):
    """Concatena os trechos mantidos. Usa filter_complex_script para suportar centenas de cortes."""
    parts, labels = [], []
    for i, (a, b) in enumerate(keeps):
        parts.append(f"[0:v]trim=start={a:.3f}:end={b:.3f},setpts=PTS-STARTPTS[v{i}]")
        labels.append(f"[v{i}]")
        if has_audio:
            d = min(0.012, (b - a) / 3)       # micro-fade nas emendas evita estalos
            parts.append(f"[0:a]atrim=start={a:.3f}:end={b:.3f},asetpts=PTS-STARTPTS,"
                         f"afade=t=in:d={d:.3f},afade=t=out:st={(b - a - d):.3f}:d={d:.3f}[a{i}]")
            labels.append(f"[a{i}]")
    n = len(keeps)
    concat = f"{''.join(labels)}concat=n={n}:v=1:a={1 if has_audio else 0}[v]" + ("[a]" if has_audio else "")
    script = ";\n".join(parts + [concat])
    script_path = Path(dst).with_suffix(".filter.txt")
    script_path.write_text(script, encoding="utf-8")
    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(src),
           "-filter_complex_script", str(script_path), "-map", "[v]"]
    if has_audio:
        cmd += ["-map", "[a]", "-c:a", "aac", "-b:a", "192k"]
    cmd += ["-c:v", "libx264", "-preset", "veryfast", "-crf", str(crf), "-g", "30", "-keyint_min", "30",
            "-pix_fmt", "yuv420p", str(dst)]
    run(cmd)
    script_path.unlink(missing_ok=True)


def process(src, dst, words=None, threshold_db=-32.0, min_silence=0.45, padding=0.10):
    """API usada pelo edit_video.py. Retorna (words_remapeadas, estatísticas)."""
    info = probe(src)
    if not info["has_audio"]:
        raise RuntimeError("Vídeo sem áudio: não há silêncio para detectar.")
    silences, duration = detect_silences(src, threshold_db, min_silence)
    keeps = keep_segments(silences, duration, padding)
    render_cut(src, dst, keeps)
    new_dur = sum(b - a for a, b in keeps)
    joins, acc = [], 0.0                       # instantes (linha do tempo final) onde houve emenda
    for a, b in keeps[:-1]:
        acc += b - a
        joins.append(round(acc, 3))
    stats = {"original_s": round(duration, 2), "final_s": round(new_dur, 2),
             "removed_s": round(duration - new_dur, 2), "cuts": len(keeps) - 1, "joins": joins}
    return (remap_words(words, keeps) if words is not None else None), stats


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input")
    ap.add_argument("-o", "--output", required=True)
    ap.add_argument("--threshold", type=float, default=-32.0, help="dB abaixo dos quais é silêncio (padrão -32)")
    ap.add_argument("--min-silence", type=float, default=0.45, help="duração mínima do silêncio em s")
    ap.add_argument("--padding", type=float, default=0.10, help="respiro mantido em cada borda da fala")
    ap.add_argument("--transcript", help="transcript.json a remapear")
    ap.add_argument("--out-transcript", help="onde salvar o transcript remapeado")
    args = ap.parse_args()

    require_ffmpeg()
    t = load_json(args.transcript) if args.transcript else None
    words, stats = process(args.input, args.output, t["words"] if t else None,
                           args.threshold, args.min_silence, args.padding)
    if t and args.out_transcript:
        save_json({**t, "words": words, "duration": stats["final_s"]}, args.out_transcript)
    print(stats)


if __name__ == "__main__":
    main()
