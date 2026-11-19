"""Monta o dash do Robô de Postagem (robo-postagem.html) a partir do código de arte dos dois dashboards.
Uso: python3 -I montar_dash.py <html_dash_alerta> <html_dash_direita>
"""
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent


def extrair(caminho):
    linhas = Path(caminho).read_text(encoding="utf-8").split("\n")
    ini = next(i for i, l in enumerate(linhas) if 'const cv = $("#cv")' in l)
    fim = next(i for i, l in enumerate(linhas) if i > ini and l.startswith("function carregarFoto"))
    bloco = linhas[ini:fim]
    if not any(l.startswith("const LOGO") for l in bloco):
        bloco = [l for l in linhas if l.startswith("const LOGO")][:1] + bloco
    return "\n".join(bloco)


def fabrica(nome, codigo):
    return f"""function {nome}(canvas){{
  const fields = {{"#fMan":{{value:""}},"#fFina":{{value:""}},"#fChapeu":{{value:""}},"#fDest":{{value:""}},"#fUrg":{{checked:false}}}};
  const $ = s => s === "#cv" ? canvas : fields[s];
  const state = {{ current:null, photo:null, photoPos:40 }};
{codigo}
  return {{ draw, state, fields, logo: LOGO }};
}}"""


modelo = (AQUI / "modelo.html").read_text(encoding="utf-8")
alerta = fabrica("marcaAlerta", extrair(sys.argv[1]))
direita = fabrica("marcaDireita", extrair(sys.argv[2]))
(AQUI / "robo-postagem.html").write_text(modelo.replace("/*%MARCAS%*/", alerta + "\n" + direita), encoding="utf-8")
print("ok")
