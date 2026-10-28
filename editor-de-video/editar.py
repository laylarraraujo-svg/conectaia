#!/usr/bin/env python3
"""Editor de vídeo do Colégio Conecta Araras.

Entra: um vídeo + o nome de um modelo (pasta modelos/) + opcionalmente fotos/vídeos extras e uma música.
Sai (em saida/<nome-do-video>/):
  video-final.mp4   vídeo editado (cortes de silêncio, legendas, títulos, gráficos, fotos/vídeos, trilha, cartão final)
  capa.jpg          capa 1080px com título, na identidade da marca
  legenda.txt       texto do post (gancho, corpo, chamada e hashtags)
  transcricao.txt   o que foi falado, com o tempo de cada frase no vídeo final (para planejar gráficos e fotos)
  resumo.json       o que foi feito (silêncio removido, onde cada foto entrou, música usada...)

Uso:
  python editar.py --listar-modelos
  python editar.py entrada/aula.mp4 --modelo conecta-reels --preparar          # 1) só transcreve e corta
  python editar.py entrada/aula.mp4 --modelo conecta-reels --midias entrada/fotos --musica musicas/trilha.mp3 \\
                   --plano entrada/aula.plano.json --rascunho                  # 2) rascunho rápido (540p)
  python editar.py entrada/aula.mp4 --modelo conecta-reels --midias entrada/fotos --musica musicas/trilha.mp3 \\
                   --plano entrada/aula.plano.json                             # 3) final

O plano (opcional) é um JSON que ajusta a edição deste vídeo. Formato em LEIA-ME.md.
"""
import argparse
import glob
import json
import os
import random
import re
import shutil
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "motor" / "scripts"))

from common import load_json, local_font, pick_font, probe, require_ffmpeg, run, save_json  # noqa: E402
from cut_silence import process as cut_process  # noqa: E402
from edit_video import PRESET_DIR, apply_replacements, deep_merge  # noqa: E402

MODELOS = ROOT / "modelos"
MUSICAS = ROOT / "musicas"
IMG_EXT = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
VID_EXT = {".mp4", ".mov", ".m4v", ".webm", ".mkv", ".avi"}
AUD_EXT = {".mp3", ".wav", ".m4a", ".aac", ".ogg", ".flac"}
STOP = set("""a o e de da do das dos em no na nos nas um uma para pra por com que se ao aos foto video img imagem
clip clipe broll final copia copy""".split())


# --------------------------------------------------------------------------- utilidades
def norm(s):
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]", "", s)


def slug(s):
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-") or "video"


def ff(*args, cwd=None):
    run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", *map(str, args)], cwd=cwd)


def find_browser():
    """O HyperFrames baixa o Chrome sozinho; se já houver um Chromium na máquina, usa ele."""
    if os.environ.get("HYPERFRAMES_BROWSER_PATH"):
        return
    for pat in ("/opt/pw-browsers/chromium-*/chrome-linux*/chrome", os.path.expanduser("~/.cache/ms-playwright/chromium-*/chrome-linux*/chrome")):
        hits = sorted(glob.glob(pat))
        if hits:
            os.environ["HYPERFRAMES_BROWSER_PATH"] = hits[-1]
            return


def listar_modelos():
    print("Modelos disponíveis (use --modelo <id>):\n")
    for f in sorted(MODELOS.glob("*.json")):
        m = load_json(f)
        print(f"  {f.stem:<16} {m.get('nome', '')}\n  {'':<16} {m.get('descricao', '')}\n")


def carregar_modelo(nome):
    path = MODELOS / f"{nome}.json"
    if not path.exists():
        sys.exit(f"Modelo '{nome}' não existe. Opções: {', '.join(f.stem for f in MODELOS.glob('*.json'))}")
    m = load_json(path)
    spec = m.get("edicao", {})
    if spec.get("preset"):
        spec = deep_merge(load_json(PRESET_DIR / f"{spec['preset']}.json"), {k: v for k, v in spec.items() if k != "preset"})
    m["edicao"] = spec
    return m


# --------------------------------------------------------------------------- etapa 1: preparar vídeo
def preparar_video(src, dst, formato):
    """Normaliza para 30 fps / GOP curto e, se o modelo pedir 9:16, recorta o centro e redimensiona para 1080x1920."""
    info = probe(src)
    W, H = info["width"], info["height"]
    if formato == "9:16":
        tw, th = 1080, 1920
        vf = f"scale={tw}:{th}:force_original_aspect_ratio=increase,crop={tw}:{th}"
    else:
        scale = min(1.0, 1920 / max(W, H))
        tw, th = int(W * scale) // 2 * 2, int(H * scale) // 2 * 2
        vf = f"scale={tw}:{th}"
    args = ["-i", src, "-vf", f"{vf},setsar=1", "-r", "30", "-c:v", "libx264", "-preset", "veryfast", "-crf", "17",
            "-g", "30", "-keyint_min", "30", "-pix_fmt", "yuv420p"]
    args += ["-c:a", "aac", "-b:a", "192k", "-ar", "48000"] if info["has_audio"] else []
    ff(*args, dst)
    return tw, th


def transcrever(video, work, spec, modelo_whisper):
    tpath = work / "transcript.json"
    if tpath.exists():
        return load_json(tpath)["words"]
    from transcribe import transcribe
    print(f"Transcrevendo com Whisper ({modelo_whisper}; a 1ª vez baixa o modelo)...")
    data = transcribe(video, modelo_whisper, spec.get("language", "pt"), spec.get("prompt"))
    save_json(data, tpath)
    return data["words"]


def cortar(video, work, words, sil):
    """Corta silêncio com cache: só refaz se o vídeo ou os parâmetros mudarem."""
    key = {"src_size": Path(video).stat().st_size, **{k: sil.get(k) for k in ("enabled", "threshold_db", "min_silence", "padding")}}
    meta_p, out = work / "corte.json", work / "cortado.mp4"
    if meta_p.exists() and out.exists():
        meta = load_json(meta_p)
        if meta.get("key") == key:
            return out, meta["words"], meta["stats"]
    if sil.get("enabled", True):
        words2, stats = cut_process(video, out, words, sil.get("threshold_db", -32), sil.get("min_silence", 0.45), sil.get("padding", 0.10))
    else:
        shutil.copy2(video, out)
        d = probe(out)["duration"]
        words2, stats = words, {"original_s": round(d, 2), "final_s": round(d, 2), "removed_s": 0, "cuts": 0, "joins": []}
    save_json({"key": key, "words": words2, "stats": stats}, meta_p)
    return out, words2, stats


def frases(words, max_gap=0.6, max_words=14):
    """Agrupa palavras em frases (para transcricao.txt e legenda automática)."""
    out, cur = [], []
    for w in words:
        if cur and (w["start"] - cur[-1]["end"] > max_gap or len(cur) >= max_words):
            out.append(cur)
            cur = []
        cur.append(w)
        if w["word"].rstrip().endswith((".", "!", "?")):
            out.append(cur)
            cur = []
    if cur:
        out.append(cur)
    return [{"inicio": round(f[0]["start"], 2), "fim": round(f[-1]["end"], 2), "texto": " ".join(x["word"] for x in f)} for f in out]


def escrever_transcricao(path, words, duracao):
    linhas = [f"Duração final: {duracao:.1f}s  (tempos já na linha do tempo do vídeo editado)\n"]
    for f in frases(words):
        linhas.append(f"[{f['inicio']:6.2f} - {f['fim']:6.2f}]  {f['texto']}")
    Path(path).write_text("\n".join(linhas) + "\n", encoding="utf-8")


# --------------------------------------------------------------------------- etapa 2: fotos e vídeos (b-roll)
def listar_midias(pasta):
    if not pasta:
        return []
    p = Path(pasta)
    files = [p] if p.is_file() else sorted(x for x in p.iterdir() if x.is_file())
    return [f for f in files if f.suffix.lower() in IMG_EXT | VID_EXT]


def palavras_chave(arquivo):
    parts = re.split(r"[\s_\-\.]+", Path(arquivo).stem)
    return [norm(p) for p in parts if len(norm(p)) >= 3 and norm(p) not in STOP and not norm(p).isdigit()]


def duracao_midia(f, cfg):
    if f.suffix.lower() in VID_EXT:
        return min(probe(f)["duration"], cfg.get("duracao_video", 3.5))
    return cfg.get("duracao_foto", 2.6)


def livre(t0, t1, ocupados, gap):
    """ocupados: (inicio, fim, eh_broll). Entre duas mídias exige 'gap'; com gráficos/títulos basta não encostar."""
    return all(t1 + (gap if br else 0.3) <= a or t0 >= b + (gap if br else 0.3) for a, b, br in ocupados)


def maior_espaco(d, ini, fim, ocupados, gap):
    """Procura o maior trecho livre que caiba d segundos; devolve o início centralizado ou None."""
    marcos = sorted({ini, fim, *[x for a, b, _ in ocupados for x in (a - gap, a - 0.3, b + 0.3, b + gap)]})
    melhor = None
    for i, g0 in enumerate(marcos):
        for g1 in marcos[i + 1:]:
            g0c, g1c = max(g0, ini), min(g1, fim)
            if g1c - g0c < d:
                continue
            s = g0c + (g1c - g0c - d) / 2
            if livre(s, s + d, ocupados, gap) and (melhor is None or g1c - g0c > melhor[0]):
                melhor = (g1c - g0c, s)
    return round(melhor[1], 2) if melhor else None


def planejar_broll(midias, words, dur, cfg, ocupados_fixos, manual):
    """Decide quando cada foto/vídeo aparece.
    1) o que o plano mandou (arquivo + inicio);
    2) arquivos cujo NOME combina com uma palavra falada (ex.: 'biblioteca.jpg' entra quando falam 'biblioteca');
    3) o resto é distribuído nos maiores trechos livres."""
    ini, fim, gap = cfg.get("evitar_inicio", 2.5), dur - cfg.get("evitar_fim", 3.0), cfg.get("intervalo_min", 3.5)
    ocupados = [(a, b, False) for a, b in ocupados_fixos]
    plano, usados = [], set()
    by_name = {m.name: m for m in midias}
    for item in manual or []:
        f = by_name.get(Path(item["arquivo"]).name) or Path(item["arquivo"])
        if not f.exists():
            print(f"AVISO: mídia do plano não encontrada: {item['arquivo']}")
            continue
        d = item.get("duracao") or duracao_midia(f, cfg)
        s = float(item["inicio"])
        plano.append({"file": f, "start": s, "duration": d, "layout": item.get("layout", cfg.get("layout", "full")), "motivo": "plano"})
        ocupados.append((s, s + d, True))
        usados.add(f.name)
    nw = [(norm(w["word"]), w["start"]) for w in words]
    resto = []
    for f in midias:
        if f.name in usados:
            continue
        d, kws, achou = duracao_midia(f, cfg), palavras_chave(f), None
        for wn, t in nw:
            if len(wn) < 3:
                continue
            if any(wn == k or (len(k) >= 4 and (wn.startswith(k[:max(4, len(k) - 2)]) or k.startswith(wn) and len(wn) >= 5)) for k in kws):
                s = max(ini, t - 0.15)
                if s + d <= fim and livre(s, s + d, ocupados, gap):
                    achou = s
                    break
        if achou is not None:
            plano.append({"file": f, "start": round(achou, 2), "duration": d, "layout": cfg.get("layout", "full"), "motivo": "palavra falada"})
            ocupados.append((achou, achou + d, True))
        else:
            resto.append((f, d))
    for f, d in resto:
        s = maior_espaco(d, ini, fim, ocupados, gap)
        if s is None:
            print(f"AVISO: sem espaço para {f.name} (vídeo curto ou muitas mídias); ficou de fora. Diminua 'intervalo_min' no modelo ou posicione no plano.")
            continue
        plano.append({"file": f, "start": s, "duration": d, "layout": cfg.get("layout", "full"), "motivo": "distribuída"})
        ocupados.append((s, s + d, True))
    return sorted(plano, key=lambda x: x["start"])


def preparar_midia(item, W, H, assets):
    """Foto: corrige rotação e reduz. Vídeo: recorta o trecho, enquadra no formato, sem áudio, 30 fps."""
    f = item["file"]
    assets.mkdir(parents=True, exist_ok=True)
    if f.suffix.lower() in VID_EXT:
        dst = assets / f"broll-{slug(f.stem)}-{int(item['start'] * 100)}.mp4"
        src_d = probe(f)["duration"]
        ss = max(0.0, (src_d - item["duration"]) / 2) if src_d > item["duration"] + 1 else 0.0   # pega o meio do clipe
        ff("-ss", f"{ss:.2f}", "-t", f"{item['duration'] + 0.3:.2f}", "-i", f,
           "-vf", f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1", "-r", "30", "-an",
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-g", "30", "-pix_fmt", "yuv420p", dst)
        return {"type": "broll", "kind": "video", "file": str(dst), "start": item["start"], "duration": item["duration"], "layout": item["layout"]}
    from PIL import Image, ImageOps
    im = ImageOps.exif_transpose(Image.open(f)).convert("RGB")
    im.thumbnail((max(W, H) * 1.3, max(W, H) * 1.3))
    dst = assets / f"broll-{slug(f.stem)}.jpg"
    im.save(dst, quality=92)
    zoom = "in" if int(item["start"] * 10) % 2 == 0 else "out"
    return {"type": "broll", "kind": "image", "file": str(dst), "start": item["start"], "duration": item["duration"], "layout": item["layout"], "zoom": zoom}


# --------------------------------------------------------------------------- etapa 3: música
def escolher_musica(arg, modelo):
    if arg:
        p = Path(arg)
        if p.is_dir():
            files = sorted(x for x in p.iterdir() if x.suffix.lower() in AUD_EXT)
            return random.choice(files) if files else None
        return p if p.exists() else None
    nome = (modelo.get("musica") or {}).get("arquivo")
    if nome and (MUSICAS / nome).exists():
        return MUSICAS / nome
    return None


def mixar_musica(video, musica, out, cfg, dur):
    """Música em loop, volume baixo, fade no começo/fim e 'ducking': abaixa sozinha quando há fala."""
    vol, fi, fo = cfg.get("volume", 0.14), cfg.get("fade_in", 0.8), cfg.get("fade_out", 2.0)
    has_voice = probe(video)["has_audio"]
    mus = (f"[1:a]aresample=48000,aformat=channel_layouts=stereo,volume={vol},afade=t=in:st=0:d={fi},"
           f"afade=t=out:st={max(dur - fo, 0):.2f}:d={fo},atrim=0:{dur:.3f}[m]")
    if has_voice and cfg.get("ducking", True):
        graph = (f"[0:a]aresample=48000,aformat=channel_layouts=stereo,asplit=2[v][sc];{mus};"
                 f"[m][sc]sidechaincompress=threshold=0.03:ratio=6:attack=20:release=350[md];"
                 f"[v][md]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.95[a]")
    elif has_voice:
        graph = f"[0:a]aresample=48000,aformat=channel_layouts=stereo[v];{mus};[v][m]amix=inputs=2:duration=first:normalize=0[a]"
    else:
        graph = f"{mus.replace('[m]', '[a]')}"
    ff("-i", video, "-stream_loop", "-1", "-i", musica, "-filter_complex", graph, "-map", "0:v", "-map", "[a]",
       "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-shortest", out)


# --------------------------------------------------------------------------- etapa 4: capa
def melhor_quadro(video, work, dur, tempo=None, evitar=()):
    """Escolhe um quadro nítido e bem iluminado nos primeiros 70% (ou usa o tempo pedido)."""
    from PIL import Image, ImageFilter, ImageStat
    cand_dir = work / "capa_quadros"
    cand_dir.mkdir(exist_ok=True)
    tempos = [tempo] if tempo is not None else [round(dur * k / 14, 2) for k in range(1, 11)]
    tempos = [t for t in tempos if tempo is not None or not any(a - 0.2 <= t <= b + 0.2 for a, b in evitar)] or [dur * 0.3]
    melhor, nota_max = None, -1
    for t in tempos:
        p = cand_dir / f"q{t:07.2f}.jpg"
        ff("-ss", f"{t:.2f}", "-i", video, "-frames:v", "1", "-q:v", "2", p)
        if not p.exists():
            continue
        im = Image.open(p).convert("L")
        im.thumbnail((540, 540))
        nitidez = ImageStat.Stat(im.filter(ImageFilter.FIND_EDGES)).var[0]
        brilho = ImageStat.Stat(im).mean[0]
        nota = nitidez * (1 - abs(brilho - 125) / 160)
        if nota > nota_max:
            melhor, nota_max = p, nota
    return melhor


def _fonte(tam, spec):
    from PIL import ImageFont
    fam = pick_font(spec.get("font"))
    hit = local_font(fam) or local_font("Montserrat")
    try:
        return ImageFont.truetype(hit[1] if hit else "DejaVuSans-Bold.ttf", tam)
    except OSError:
        return ImageFont.load_default()


def _quebrar(draw, palavras, fonte, largura):
    """Quebra o título em linhas de largura parecida (evita uma palavra sozinha numa linha)."""
    def greedy(lim):
        linhas, cur = [], []
        for p in palavras:
            if cur and draw.textlength(" ".join(x for x, _ in cur + [p]), font=fonte) > lim:
                linhas.append(cur)
                cur = []
            cur.append(p)
        return linhas + ([cur] if cur else [])
    base = greedy(largura)
    n = len(base)
    total = draw.textlength(" ".join(x for x, _ in palavras), font=fonte)
    lim = total / n
    while lim < largura:
        tent = greedy(lim)
        if len(tent) <= n:
            return tent
        lim += largura * 0.02
    return base


def gerar_capa(quadro, out, titulo, modelo, spec):
    """Capa na identidade da marca. O texto fica na faixa central (área que aparece no grid 3:4 do Instagram).
    Use *palavra* no título para pintar de amarelo."""
    from PIL import Image, ImageDraw, ImageFilter
    th = spec.get("theme", {})
    accent, texto, brand = th.get("accent", "#F9C700"), th.get("text", "#FFFFFF"), th.get("brand", "#224289")
    cfg = modelo.get("capa") or {}
    estilo, selo = cfg.get("estilo", "faixa"), cfg.get("selo", "")
    base = Image.open(quadro).convert("RGB")
    W, H = base.size
    if W / H > 0.6:     # vídeo horizontal: capa 1920x1080 mantém o quadro
        pass
    img = base.copy()
    d = ImageDraw.Draw(img, "RGBA")
    hex2 = lambda h, a=255: tuple(int(h.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4)) + (a,)
    vertical = H > W
    palavras = []
    for parte in re.split(r"(\*[^*]+\*)", titulo.strip()):
        if not parte:
            continue
        dest = parte.startswith("*")
        palavras += [(w.upper(), dest) for w in parte.strip("*").split()]
    tam = int((0.072 if vertical else 0.095) * H) if len(palavras) <= 6 else int((0.058 if vertical else 0.08) * H)
    fonte = _fonte(tam, spec)
    largura = W * 0.84
    linhas = _quebrar(d, palavras, fonte, largura)
    orfa = lambda ls: any(len(l) == 1 and len(l[0][0]) <= 4 for l in ls) and len(ls) > 1
    tam0 = tam
    while (len(linhas) > 4 or orfa(linhas)) and tam > max(40, tam0 * 0.72):
        tam = int(tam * 0.88)
        fonte = _fonte(tam, spec)
        linhas = _quebrar(d, palavras, fonte, largura)
    lh = int(tam * 1.18)
    bloco = lh * len(linhas)
    cy = H * (0.60 if vertical else 0.62)              # centro do bloco de texto
    y0 = int(cy - bloco / 2)

    if estilo == "faixa":                              # degradê escuro de baixo para cima
        grad = Image.new("L", (1, H))
        for y in range(H):
            grad.putpixel((0, y), int(235 * max(0, min(1, (y - H * 0.30) / (H * 0.45)))))
        sombra = Image.new("RGBA", (W, H), hex2(brand, 255))
        sombra.putalpha(grad.resize((W, H)))
        img.paste(sombra, (0, 0), sombra)
    elif estilo == "limpo":                            # leve escurecida geral
        img = Image.blend(img, Image.new("RGB", img.size, (10, 14, 30)), 0.35)
    else:                                              # impacto: fundo levemente desfocado atrás do texto
        faixa = img.crop((0, y0 - tam, W, y0 + bloco + tam)).filter(ImageFilter.GaussianBlur(12))
        img.paste(faixa, (0, y0 - tam))
    d = ImageDraw.Draw(img, "RGBA")

    for li, linha in enumerate(linhas):
        txt = " ".join(w for w, _ in linha)
        lw = d.textlength(txt, font=fonte)
        x = (W - lw) / 2
        y = y0 + li * lh
        if estilo == "impacto":
            pad = tam * 0.18
            cor_caixa = accent if any(dst for _, dst in linha) else brand
            d.rounded_rectangle((x - pad * 1.6, y - pad * 0.6, x + lw + pad * 1.6, y + tam * 1.02 + pad * 0.4), radius=int(tam * 0.18), fill=hex2(cor_caixa, 245))
        for w, dst in linha:
            cor = (brand if estilo == "impacto" and any(dd for _, dd in linha) else accent if dst else texto)
            if estilo != "impacto":
                d.text((x + tam * 0.04, y + tam * 0.06), w, font=fonte, fill=(0, 0, 0, 140))
            d.text((x, y), w, font=fonte, fill=hex2(cor))
            x += d.textlength(w + " ", font=fonte)

    if selo:
        fs = _fonte(int(tam * 0.36), spec)
        sw = d.textlength(selo, font=fs)
        sy = y0 + bloco + int(tam * 0.45)
        d.rectangle(((W - sw) / 2 - tam * 0.5, sy + tam * 0.18, (W - sw) / 2 - tam * 0.2, sy + tam * 0.26), fill=hex2(accent))
        d.rectangle(((W + sw) / 2 + tam * 0.2, sy + tam * 0.18, (W + sw) / 2 + tam * 0.5, sy + tam * 0.26), fill=hex2(accent))
        d.text(((W - sw) / 2, sy), selo, font=fs, fill=hex2(texto))
    img.save(out, quality=93)
    return out


# --------------------------------------------------------------------------- etapa 5: legenda do post
def gerar_legenda(words, gancho, modelo):
    """Rascunho automático. O ideal é o Claude (Agente Marketing) escrever a legenda final no plano."""
    texto = " ".join(w["word"] for w in words).strip()
    fr = [x for x in re.split(r"(?<=[.!?])\s+", texto) if x]
    abertura = gancho.replace("*", "") if gancho else (fr[0] if fr else "")
    corpo = " ".join(fr[:3] if gancho else fr[1:4])
    if len(corpo) > 380:
        corpo = corpo[:380].rsplit(" ", 1)[0] + "..."
    cfg = modelo.get("legenda") or {}
    partes = [abertura, corpo, cfg.get("cta", ""), " ".join(cfg.get("hashtags", []))]
    return "\n\n".join(p for p in partes if p).strip() + "\n"


# --------------------------------------------------------------------------- principal
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video", nargs="?")
    ap.add_argument("--modelo", default="conecta-reels", help="id do modelo (veja --listar-modelos)")
    ap.add_argument("--midias", help="pasta (ou arquivo) com fotos e vídeos para inserir")
    ap.add_argument("--musica", help="arquivo de música (ou pasta: sorteia uma). Sem isso, vai sem trilha")
    ap.add_argument("--plano", help="JSON com ajustes deste vídeo (gancho, gráficos, fotos, capa, legenda)")
    ap.add_argument("--saida", help="pasta de saída (padrão: saida/<nome-do-video>)")
    ap.add_argument("--preparar", action="store_true", help="só transcreve e corta; gera transcricao.txt para planejar")
    ap.add_argument("--rascunho", action="store_true", help="render rápido em 540p para conferir")
    ap.add_argument("--titulo-capa", help="título da capa (use *palavra* para destacar)")
    ap.add_argument("--whisper", default="small", help="modelo do Whisper: tiny/base/small/medium/large-v3")
    ap.add_argument("--listar-modelos", action="store_true")
    a = ap.parse_args()

    if a.listar_modelos or not a.video:
        listar_modelos()
        return
    require_ffmpeg()
    find_browser()

    modelo = carregar_modelo(a.modelo)
    plano = load_json(a.plano) if a.plano else {}
    spec = deep_merge(modelo["edicao"], plano.get("edicao", {}))
    if plano.get("substituicoes"):
        spec["replacements"] = {**spec.get("replacements", {}), **plano["substituicoes"]}
    if plano.get("vocabulario"):
        spec["prompt"] = plano["vocabulario"]

    src = Path(a.video).resolve()
    saida = Path(a.saida).resolve() if a.saida else ROOT / "saida" / slug(src.stem)
    work = saida / "_trabalho"
    work.mkdir(parents=True, exist_ok=True)

    # 1) preparar + transcrever + cortar
    prep = work / f"preparado-{slug(modelo.get('formato', 'original'))}.mp4"
    if not prep.exists():
        print("Preparando vídeo...")
        preparar_video(src, prep, modelo.get("formato", "original"))
    info = probe(prep)
    W, H = info["width"], info["height"]
    words = transcrever(prep, work, spec, a.whisper) if info["has_audio"] else []
    sil = spec.get("silence", {}) if info["has_audio"] else {"enabled": False}
    cortado, words, stats = cortar(prep, work, words, sil)
    words = apply_replacements(words, spec.get("replacements"))
    dur = probe(cortado)["duration"]
    escrever_transcricao(saida / "transcricao.txt", words, dur)
    print(f"Silêncio removido: {stats['removed_s']}s ({stats['original_s']}s -> {stats['final_s']}s, {stats['cuts']} cortes)")
    if a.preparar:
        print(f"Transcrição pronta: {saida / 'transcricao.txt'}")
        return

    # 2) overlays: gancho, apresentação, plano, b-roll, encerramento
    overlays = []
    gancho = plano.get("gancho")
    gcfg = modelo.get("gancho") or {}
    if gancho:
        overlays.append({"type": "title", "text": gancho, "start": 0.15, "duration": gcfg.get("duracao", 2.6), "position": gcfg.get("posicao", "top")})
    if plano.get("pessoa"):        # lower third (nome + papel), útil no modelo depoimento
        ap_cfg = modelo.get("apresentacao") or {"inicio": 0.6, "duracao": 3.5}
        overlays.append({"type": "lower_third", "title": plano["pessoa"].get("nome", ""), "subtitle": plano["pessoa"].get("papel", ""),
                         "start": ap_cfg["inicio"], "duration": ap_cfg["duracao"]})
    overlays += plano.get("overlays", [])
    enc = plano.get("encerramento", modelo.get("encerramento"))
    end_start = dur
    if enc:
        end_start = max(0.5, dur - enc.get("duracao", 2.6))
        overlays.append({"type": "end_card", "text": enc.get("texto", ""), "subtext": enc.get("subtexto", ""),
                         "start": round(end_start, 2), "duration": round(dur - end_start, 2)})
    fixos = [(o["start"], o["start"] + o["duration"]) for o in overlays if o.get("type") in ("pillars", "end_card", "chart", "stat", "cards", "numbered_title")]
    midias = listar_midias(a.midias)
    bcfg = {**modelo.get("broll", {}), **({"layout": plano["broll_layout"]} if plano.get("broll_layout") else {})}
    broll = planejar_broll(midias, words, end_start if enc else dur, bcfg, fixos, plano.get("broll"))
    for item in broll:
        overlays.append(preparar_midia(item, W, H, work / "midias"))

    # 3) render (HyperFrames)
    from hf_project import build_project, render
    hf = work / "hf"
    if hf.exists():
        shutil.rmtree(hf)
    build_project(hf, cortado, words, {**spec, "overlays": overlays, "subtitles": {**spec.get("subtitles", {}), "enabled": bool(words) and spec.get("subtitles", {}).get("enabled", True)}},
                  stats.get("joins", []))
    sem_musica = work / ("render-rascunho.mp4" if a.rascunho else "render.mp4")
    print(f"Renderizando {'rascunho ' if a.rascunho else ''}({len(overlays)} elementos na tela, {dur:.1f}s)...")
    try:
        render(hf, sem_musica, draft=a.rascunho)
    except RuntimeError as e:
        sys.exit(str(e))

    final = saida / ("video-rascunho.mp4" if a.rascunho else "video-final.mp4")
    musica = escolher_musica(a.musica, modelo)
    if musica:
        print(f"Mixando trilha: {musica.name}")
        mixar_musica(sem_musica, musica, final, {**(modelo.get("musica") or {}), **plano.get("musica", {})}, probe(sem_musica)["duration"])
    else:
        shutil.copy2(sem_musica, final)

    # 4) capa
    capa_cfg = plano.get("capa", {})
    titulo = a.titulo_capa or capa_cfg.get("titulo") or gancho or (frases(words)[0]["texto"] if words else modelo.get("nome", ""))
    if capa_cfg.get("estilo"):
        modelo["capa"] = {**(modelo.get("capa") or {}), "estilo": capa_cfg["estilo"]}
    evitar = [(b["start"], b["start"] + b["duration"]) for b in broll] + ([(end_start, dur)] if enc else [])
    quadro = Path(capa_cfg["imagem"]) if capa_cfg.get("imagem") else melhor_quadro(cortado, work, dur, capa_cfg.get("tempo"), evitar)
    gerar_capa(quadro, saida / "capa.jpg", titulo, modelo, spec)

    # 5) legenda do post
    legenda = plano.get("legenda") or gerar_legenda(words, gancho, modelo)
    (saida / "legenda.txt").write_text(legenda if legenda.endswith("\n") else legenda + "\n", encoding="utf-8")

    resumo = {
        "modelo": a.modelo, "video_final": str(final), "capa": str(saida / "capa.jpg"), "legenda": str(saida / "legenda.txt"),
        "duracao_s": round(probe(final)["duration"], 1), "resolucao": f"{W}x{H}",
        "silencio_removido_s": stats["removed_s"], "cortes": stats["cuts"],
        "midias": [{"arquivo": b["file"].name, "inicio": b["start"], "duracao": b["duration"], "por": b["motivo"]} for b in broll],
        "musica": musica.name if musica else None, "legenda_automatica": not plano.get("legenda"),
        "titulo_capa": titulo,
    }
    save_json(resumo, saida / "resumo.json")
    print("\nPronto!")
    print(f"  Vídeo:   {final}")
    print(f"  Capa:    {saida / 'capa.jpg'}")
    print(f"  Legenda: {saida / 'legenda.txt'}" + ("  (rascunho automático: revise)" if resumo["legenda_automatica"] else ""))
    for b in resumo["midias"]:
        print(f"  Mídia {b['arquivo']} em {b['inicio']}s ({b['por']})")


if __name__ == "__main__":
    main()
