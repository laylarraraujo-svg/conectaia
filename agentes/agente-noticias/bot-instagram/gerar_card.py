"""Gera o card (JPEG 1080x1350) de uma notícia para o Instagram.

Uso:
  python3 gerar_card.py saida.jpg "CATEGORIA" "Título" "Resumo curto" "Fonte" "19/11/2026"
"""
import sys
import textwrap
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1350
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_REG = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

CORES = {  # cor da faixa por categoria
    "SEGURANÇA": (200, 40, 40),
    "TRÂNSITO": (230, 120, 0),
    "OBRAS": (230, 120, 0),
    "SAÚDE": (0, 140, 110),
    "SERVIÇOS": (20, 110, 190),
    "PREFEITURA": (90, 60, 170),
    "CÂMARA": (90, 60, 170),
    "ECONOMIA": (30, 130, 60),
    "EMPREGO": (30, 130, 60),
    "EVENTOS": (190, 50, 130),
    "CLIMA": (40, 140, 200),
}


def quebra(draw, texto, fonte, largura):
    """Quebra o texto em linhas que cabem na largura em pixels."""
    linhas = []
    for par in texto.split("\n"):
        palavras, atual = par.split(), ""
        for p in palavras:
            teste = (atual + " " + p).strip()
            if draw.textlength(teste, font=fonte) <= largura:
                atual = teste
            else:
                linhas.append(atual)
                atual = p
        linhas.append(atual)
    return linhas


def gerar(saida, categoria, titulo, resumo, fonte, data):
    img = Image.new("RGB", (W, H), (14, 22, 40))
    d = ImageDraw.Draw(img)
    cor = CORES.get(categoria.upper(), (20, 110, 190))
    m = 80

    # cabeçalho
    d.rectangle([0, 0, W, 150], fill=(8, 14, 28))
    d.text((m, 50), "NOTÍCIAS DE MOGI GUAÇU", font=ImageFont.truetype(FONT_BOLD, 40), fill=(255, 255, 255))

    # etiqueta da categoria
    fcat = ImageFont.truetype(FONT_BOLD, 34)
    lw = d.textlength(categoria.upper(), font=fcat)
    d.rounded_rectangle([m, 220, m + lw + 48, 285], radius=12, fill=cor)
    d.text((m + 24, 232), categoria.upper(), font=fcat, fill=(255, 255, 255))

    # título (diminui a fonte até caber)
    y = 330
    for tam in (76, 68, 60, 54, 48):
        ft = ImageFont.truetype(FONT_BOLD, tam)
        lt = quebra(d, titulo, ft, W - 2 * m)
        if len(lt) * tam * 1.2 <= 560:
            break
    for linha in lt:
        d.text((m, y), linha, font=ft, fill=(255, 255, 255))
        y += int(tam * 1.2)

    # linha de destaque
    y += 25
    d.rectangle([m, y, m + 140, y + 8], fill=cor)
    y += 45

    # resumo
    fr = ImageFont.truetype(FONT_REG, 40)
    for linha in quebra(d, resumo, fr, W - 2 * m)[:8]:
        d.text((m, y), linha, font=fr, fill=(215, 222, 235))
        y += 54

    # rodapé
    d.rectangle([0, H - 130, W, H], fill=(8, 14, 28))
    ff = ImageFont.truetype(FONT_REG, 32)
    d.text((m, H - 88), f"Fonte: {fonte}", font=ff, fill=(200, 205, 215))
    dw = d.textlength(data, font=ff)
    d.text((W - m - dw, H - 88), data, font=ff, fill=(200, 205, 215))

    img.save(saida, "JPEG", quality=88)


if __name__ == "__main__":
    gerar(*sys.argv[1:7])
