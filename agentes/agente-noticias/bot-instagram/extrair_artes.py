"""Extrai dos dashboards (artifacts) o código que desenha a arte dos posts
e monta uma página de renderização por marca: render-alerta.html e render-direita.html.

Uso: python3 -I extrair_artes.py <html_dash_alerta> <html_dash_direita>
"""
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent

MODELO = """<!doctype html><html><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@600;700;800;900&family=Barlow:wght@400;500;600;700&family=Chakra+Petch:wght@500;600;700&display=swap" rel="stylesheet">
</head><body style="margin:0;background:#000">
<canvas id="cv" width="1080" height="1350"></canvas>
<input id="fMan"><input id="fFina"><input id="fChapeu"><input id="fDest"><input id="fUrg" type="checkbox">
<script>
const $ = s => document.querySelector(s);
const state = { current: null, photo: null, photoPos: 40 };
%CODIGO%
window.renderizar = async (n) => {
  $("#fMan").value = n.manchete || ""; $("#fFina").value = n.linha_fina || "";
  $("#fChapeu").value = n.chapeu || ""; $("#fDest").value = n.destaque || ""; $("#fUrg").checked = !!n.urgente;
  state.current = { id: n.id || n.manchete, categoria: n.categoria || "", titulo: n.manchete || "" };
  state.photo = null;
  await document.fonts.ready;
  for (const f of ['800 60px "Barlow Condensed"','500 30px "Barlow"','800 30px "Barlow"','700 28px "Chakra Petch"','600 24px "Barlow"','700 30px "Chakra Petch"','700 26px "Chakra Petch"']) { try { await document.fonts.load(f); } catch(e){} }
  if (!LOGO.complete) await new Promise(r => { LOGO.onload = r; LOGO.onerror = r; });
  draw();
  return cv.toDataURL("image/jpeg", 0.9);
};
</script></body></html>"""


def extrair(caminho):
    linhas = Path(caminho).read_text(encoding="utf-8").split("\n")
    ini = next(i for i, l in enumerate(linhas) if 'const cv = $("#cv")' in l)
    fim = next(i for i, l in enumerate(linhas) if i > ini and l.startswith("function carregarFoto"))
    bloco = linhas[ini:fim]
    # o LOGO pode estar declarado antes do bloco (dash alerta)
    if not any(l.startswith("const LOGO") for l in bloco):
        bloco = [l for l in linhas if l.startswith("const LOGO")][:1] + bloco
    return "\n".join(bloco)


if __name__ == "__main__":
    for nome, cam in (("alerta", sys.argv[1]), ("direita", sys.argv[2])):
        (AQUI / f"render-{nome}.html").write_text(MODELO.replace("%CODIGO%", extrair(cam)), encoding="utf-8")
        print("ok", nome)
