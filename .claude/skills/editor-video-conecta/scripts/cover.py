#!/usr/bin/env python3
"""Cria a capa (thumbnail) do Reel: um quadro do vídeo + título grande, sem cobrir o rosto.

- Escolhe sozinho o melhor quadro (rosto grande, nítido e de frente), ou use --time.
- O título fica fora do rosto e dentro da área que aparece no grade do perfil (recorte 3:4 central).
- Linhas com *asteriscos* saem em amarelo e maiores (palavra-chave).

Uso:
  python cover.py video.mp4 -o capa.png --title "Licitação das ambulâncias|*IMPUGNADA*|pela 4ª vez"
  python cover.py video.mp4 -o capa.png --title "..." --time 12.5 --tag "MOGI GUAÇU"
"""
import argparse
import base64
import html
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import local_font, pick_font, text_width

ACCENT = "#F9D41A"


def best_frame(video, time=None, samples=40):
    """Retorna (quadro BGR, caixa do rosto normalizada ou None)."""
    import cv2
    from face_track import MODEL, GROW_BOTTOM, GROW_SIDE, GROW_TOP
    cap = cv2.VideoCapture(str(video))
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    W, H = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    sc = 480 / max(W, H)
    det = cv2.FaceDetectorYN.create(str(MODEL), "", (int(W * sc), int(H * sc)), 0.6, 0.3, 5)
    idxs = [int(time * fps)] if time is not None else [int(n * (0.05 + 0.9 * k / (samples - 1))) for k in range(samples)]
    best = None
    for i in idxs:
        cap.set(cv2.CAP_PROP_POS_FRAMES, i)
        ok, fr = cap.read()
        if not ok:
            continue
        small = cv2.resize(fr, (int(W * sc), int(H * sc)))
        _, faces = det.detect(small)
        box, score = None, 0.0
        if faces is not None and len(faces):
            f = max(faces, key=lambda f: f[2] * f[3])
            x, y, bw, bh = (float(v) for v in f[:4])
            gray = cv2.cvtColor(fr, cv2.COLOR_BGR2GRAY)
            x0, y0 = int(x / sc), int(y / sc)
            crop = gray[max(0, y0):y0 + int(bh / sc), max(0, x0):x0 + int(bw / sc)]
            sharp = cv2.Laplacian(crop, cv2.CV_64F).var() if crop.size else 0
            # olhos na mesma altura = rosto de frente; nitidez e confiança do detector pesam também
            eyes_level = 1 - min(1, abs(float(f[5]) - float(f[7])) / max(bh * 0.25, 1))
            score = float(f[14]) * (1 + sharp ** 0.5 / 10) * (0.5 + eyes_level)
            w, h = small.shape[1], small.shape[0]
            box = (max(0, (x - bw * GROW_SIDE) / w), max(0, (y - bh * GROW_TOP) / h),
                   min(1, (x + bw * (1 + GROW_SIDE)) / w), min(1, (y + bh * (1 + GROW_BOTTOM)) / h))
        if best is None or score > best[0]:
            best = (score, fr, box)
    cap.release()
    if best is None:
        sys.exit("Não consegui ler quadros do vídeo.")
    return best[1], best[2]


def layout(lines, face, W, H, family, base):
    """Escolhe tamanho e posição do bloco de texto: abaixo do rosto (preferido) ou acima, dentro da área 3:4."""
    safe0, safe1 = (H - W * 4 / 3) / 2 + 0.03 * H, (H + W * 4 / 3) / 2 - 0.03 * H   # recorte do grade do perfil
    m = 0.02 * H
    zones = [(safe0, safe1)]
    if face:
        fy0, fy1 = face[1] * H, face[3] * H
        zones = [(max(safe0, fy1 + m), safe1), (safe0, min(safe1, fy0 - m))]
    for size in [base * k for k in (1, 0.9, 0.8, 0.7, 0.6, 0.5)]:
        hs = [size * (1.45 if key else 1) * 1.05 for _, key in lines]
        ws = [text_width(t.upper() if key else t, size * (1.45 if key else 1), family) for t, key in lines]
        if max(ws) > 0.9 * W:
            continue
        need = sum(hs)
        for z0, z1 in zones:
            if z1 - z0 >= need:
                return size, (z0 + z1 - need) / 2
    return base * 0.5, safe1 - base


def render_html(img_b64, lines, size, top, W, H, family, face_css, tag):
    rows = "".join(
        f'<div class="{"k" if key else "t"}">{html.escape(t)}</div>' for t, key in lines)
    tag_html = f'<div class="tag">{html.escape(tag)}</div>' if tag else ""
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
{face_css}
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:{W}px;height:{H}px;overflow:hidden;background:#000}}
.bg{{position:absolute;inset:0;background:url(data:image/jpeg;base64,{img_b64}) center/cover}}
.shade{{position:absolute;left:0;right:0;top:{top - 0.12 * H:.0f}px;height:{H}px;
  background:linear-gradient(180deg,rgba(0,0,0,0),rgba(0,0,0,.62) 18%,rgba(0,0,0,.72))}}
.box{{position:absolute;left:0;width:100%;top:{top:.0f}px;text-align:center;font-family:"{family}","Montserrat",Arial,sans-serif}}
.t{{color:#fff;font-size:{size:.0f}px;line-height:1.05;text-shadow:0 4px 14px rgba(0,0,0,.6)}}
.k{{color:{ACCENT};font-size:{size * 1.45:.0f}px;line-height:1.05;text-transform:uppercase;
  text-shadow:0 0 22px rgba(249,212,26,.45),0 5px 14px rgba(0,0,0,.6)}}
.tag{{display:inline-block;margin-bottom:{size * 0.35:.0f}px;padding:{size * 0.12:.0f}px {size * 0.35:.0f}px;border-radius:{size * 0.2:.0f}px;
  background:{ACCENT};color:#111;font-size:{size * 0.42:.0f}px;letter-spacing:.06em}}
</style></head><body><div class="bg"></div><div class="shade"></div>
<div class="box">{tag_html}{rows}</div></body></html>"""


def shot(page, out, W, H):
    """Tira o 'print' da página com o Chrome headless (mesmo Chrome do HyperFrames)."""
    import os
    import shutil
    import subprocess
    import tempfile
    exe = os.environ.get("HYPERFRAMES_BROWSER_PATH") or next(
        (p for p in ("/opt/pw-browsers/chromium", shutil.which("chromium"), shutil.which("google-chrome"),
                     shutil.which("chromium-browser")) if p and Path(p).exists()), None)
    if not exe:
        sys.exit("Chrome não encontrado. Defina HYPERFRAMES_BROWSER_PATH.")
    with tempfile.TemporaryDirectory() as td:
        page_path = Path(td) / "capa.html"
        page_path.write_text(page, encoding="utf-8")
        png = Path(td) / "capa.png"
        subprocess.run([exe, "--headless=new", "--no-sandbox", "--disable-gpu", "--hide-scrollbars",
                        "--force-device-scale-factor=1", f"--window-size={W},{H}", "--virtual-time-budget=1500",
                        f"--screenshot={png}", page_path.as_uri()], capture_output=True, timeout=120)
        if not png.exists():
            sys.exit("Falha ao gerar a capa no Chrome.")
        if out.suffix.lower() in (".jpg", ".jpeg"):
            from PIL import Image
            Image.open(png).convert("RGB").save(out, quality=92)
        else:
            shutil.copy2(png, out)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video")
    ap.add_argument("-o", "--output", required=True)
    ap.add_argument("--title", required=True, help='linhas separadas por "|"; *linha* = palavra-chave amarela')
    ap.add_argument("--time", type=float, help="segundo do quadro (padrão: escolhe o melhor)")
    ap.add_argument("--tag", help="etiqueta amarela pequena acima do título (opcional)")
    ap.add_argument("--font", default="Cal Sans")
    ap.add_argument("--size", type=float, default=0.052, help="corpo do texto como fração da altura")
    a = ap.parse_args()

    import cv2
    frame, face = best_frame(a.video, a.time)
    H0, W0 = frame.shape[:2]
    W, H = (1080, 1920) if W0 < H0 else (1920, 1080)
    frame = cv2.resize(frame, (W, H), interpolation=cv2.INTER_LANCZOS4)
    ok, jpg = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 94])
    lines = [(m.group(1), True) if (m := re.fullmatch(r"\*(.+)\*", ln.strip())) else (ln.strip(), False)
             for ln in a.title.split("|") if ln.strip()]
    family = pick_font(a.font)
    hit = local_font(a.font)
    face_css = (f'@font-face{{font-family:"{hit[0]}";src:url("data:font/ttf;base64,'
                f'{base64.b64encode(Path(hit[1]).read_bytes()).decode()}")}}') if hit else ""
    size, top = layout(lines, face, W, H, family, a.size * H)
    if a.tag:
        top -= size * 0.42 * 1.6 + size * 0.35
    page = render_html(base64.b64encode(jpg.tobytes()).decode(), lines, size, top, W, H, family, face_css, a.tag)
    shot(page, Path(a.output), W, H)
    where = f"rosto em {face[1] * 100:.0f}–{face[3] * 100:.0f}% da altura" if face else "nenhum rosto achado"
    print(f"Capa: {a.output} ({W}x{H}; título a partir de {top / H * 100:.0f}% da altura; {where})")


if __name__ == "__main__":
    main()
