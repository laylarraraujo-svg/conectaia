"""Funções utilitárias compartilhadas pelos scripts do video-editor."""
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path


def run(cmd, cwd=None, capture=False, check=True):
    """Executa um comando. Em caso de erro mostra o final do stderr do ffmpeg."""
    res = subprocess.run(
        cmd, cwd=cwd, text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None,
    )
    if check and res.returncode != 0:
        tail = (res.stderr or "")[-1500:]
        raise RuntimeError(f"Comando falhou ({res.returncode}): {' '.join(map(str, cmd[:6]))}...\n{tail}")
    return res


def require_ffmpeg():
    for tool in ("ffmpeg", "ffprobe"):
        if not shutil.which(tool):
            sys.exit(f"'{tool}' não encontrado. Instale o FFmpeg (https://ffmpeg.org) e tente de novo.")


def probe(path):
    """Retorna width, height (já considerando rotação), duration, fps e has_audio."""
    res = run(["ffprobe", "-v", "error", "-print_format", "json",
               "-show_streams", "-show_format", str(path)], capture=True)
    data = json.loads(res.stdout)
    vs = next((s for s in data["streams"] if s["codec_type"] == "video"), None)
    if vs is None:
        raise RuntimeError("O arquivo não tem faixa de vídeo.")
    w, h = int(vs["width"]), int(vs["height"])
    rot = 0
    for sd in vs.get("side_data_list", []) or []:
        if "rotation" in sd:
            rot = int(sd["rotation"])
    rot = rot or int(vs.get("tags", {}).get("rotate", 0) or 0)
    if abs(rot) % 180 == 90:
        w, h = h, w
    num, _, den = (vs.get("r_frame_rate") or "30/1").partition("/")
    fps = float(num) / float(den or 1) if float(den or 1) else 30.0
    duration = float(data["format"].get("duration") or vs.get("duration") or 0)
    has_audio = any(s["codec_type"] == "audio" for s in data["streams"])
    return {"width": w, "height": h, "duration": duration, "fps": fps, "has_audio": has_audio}


def ass_time(t):
    t = max(0.0, t)
    cs = int(round(t * 100))
    h, cs = divmod(cs, 360000)
    m, cs = divmod(cs, 6000)
    s, cs = divmod(cs, 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def hex_to_ass(color, alpha=0):
    """'#FFD60A' -> '&H000AD6FF' (ASS usa BGR; alpha 0 = opaco, 255 = transparente)."""
    c = color.lstrip("#")
    r, g, b = c[0:2], c[2:4], c[4:6]
    return f"&H{alpha:02X}{b}{g}{r}".upper()


def hex_to_ass_c(color):
    """Versão sem canal alpha, para tags inline \\c: '&HBBGGRR&'."""
    c = color.lstrip("#")
    return f"&H{c[4:6]}{c[2:4]}{c[0:2]}&".upper()


def _fc_families():
    if not shutil.which("fc-list"):
        return set()
    out = subprocess.run(["fc-list", ":", "family"], text=True, capture_output=True).stdout
    fams = set()
    for line in out.splitlines():
        for f in line.split(","):
            fams.add(f.strip())
    return fams


_WARNED = set()
FONTS_DIR = Path(__file__).resolve().parent.parent / "fonts"   # solte aqui arquivos .ttf/.otf da marca


def _norm(s):
    return re.sub(r"[^a-z0-9]", "", s.lower())


def local_font(name):
    """Procura em fonts/ um arquivo cujo nome ou família combine com 'name' (ignora maiúsculas, hífen, espaço).
    Retorna (família, caminho) ou None."""
    if not name or not FONTS_DIR.exists():
        return None
    want = _norm(name)
    for f in sorted(FONTS_DIR.iterdir()):
        if f.suffix.lower() not in (".ttf", ".otf"):
            continue
        try:
            from PIL import ImageFont
            family, style = ImageFont.truetype(str(f), 20).getname()
        except Exception:
            family, style = f.stem, ""
        keys = {_norm(f.stem), _norm(family), _norm(f"{family}{style}")}
        if want in keys or any(k.startswith(want) or want.startswith(k) for k in keys if len(k) > 3):
            return family, str(f)
    return None


def pick_font(preferred=None):
    """Escolhe uma fonte: arquivo local em fonts/, fonte instalada, ou fallback. Retorna o nome da família."""
    hit = local_font(preferred)
    if hit:
        return hit[0]
    if preferred and preferred not in _WARNED and not (_fc_families() and preferred in _fc_families()):
        _WARNED.add(preferred)
        print(f"AVISO: fonte '{preferred}' não encontrada (nem em {FONTS_DIR} nem instalada). "
              f"Usando fonte substituta; coloque o arquivo .ttf/.otf em fonts/ para usar a original.",
              file=sys.stderr)
    fams = _fc_families()
    candidates = [preferred] if preferred else []
    candidates += ["Montserrat", "Poppins", "Inter", "Arial", "Helvetica", "DejaVu Sans"]
    for c in candidates:
        if c and (not fams or c in fams):
            return c
    return "Arial"


def font_path(family, bold=True):
    """Caminho do arquivo da fonte (para medir texto e para o matplotlib)."""
    hit = local_font(family)
    if hit:
        return hit[1]
    try:
        from matplotlib import font_manager as fm
        return fm.findfont(fm.FontProperties(family=family, weight="bold" if bold else "normal"),
                           fallback_to_default=True)
    except Exception:
        return None


def text_width(text, size, family, bold=True):
    """Largura aproximada em pixels do texto (usa Pillow quando possível)."""
    try:
        from PIL import ImageFont
        p = font_path(family, bold)
        if p:
            return ImageFont.truetype(p, int(size)).getlength(text)
    except Exception:
        pass
    return len(text) * size * 0.56


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_json(obj, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def punch_schedule(duration, joins, cfg):
    """Segmentos (início, fim, zoom) para o efeito de zoom alternado a cada corte."""
    levels = cfg.get("levels", [1.0, 1.14, 1.0, 1.26])
    max_hold, min_hold = cfg.get("max_hold", 4.0), cfg.get("min_hold", 1.2)
    marks = [0.0]
    for j in sorted(joins):
        if j - marks[-1] >= min_hold:
            marks.append(j)
    filled = []
    for a, b in zip(marks, marks[1:] + [duration]):
        filled.append(a)
        t = a + max_hold
        while b - t > min_hold:
            filled.append(t)
            t += max_hold
    filled.append(duration + 1)
    return [(a, b, levels[i % len(levels)]) for i, (a, b) in enumerate(zip(filled, filled[1:]))]
