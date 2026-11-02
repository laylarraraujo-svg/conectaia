"""Tela dividida (formato "dividido"): painel animado na metade de baixo e legenda em duas camadas.

Estilo "cinema" (referência do cliente): fundo quase preto com um toque de azul, ícones em traço fino, texto
principal em grotesca pesada (Inter Display Black) e palavras de efeito em serifada itálica (Playfair Display),
glitch pontual em palavras de impacto. Nada é desenhado sobre o rosto: o painel ocupa só a metade de baixo e a legenda
fica no pé do vídeo de cima, logo acima da divisória.

Tipos de overlay: alerta, icones, carimbo, palavra, lista_x, tentativas, faixas.
Em textos, *palavra* sai em serifada itálica na cor de destaque.
"""
import html
import re
import shutil
from pathlib import Path

VERMELHO = "#E5242B"
SANS = "'Inter Display',Inter,Montserrat,sans-serif"      # aspas simples: o texto vai dentro de style="..."
SERIF = "'Playfair Display',Georgia,serif"
FONTES = {"Inter Display": [("InterDisplay-Black.otf", 900), ("InterDisplay-SemiBold.otf", 600)],
          "Playfair Display": [("PlayfairDisplay-Italic.ttf", 400)]}


def esc(s):
    return html.escape(str(s), quote=True)


def rico(texto, cor):
    """Texto normal na grotesca; *trechos* em serifada itálica na cor de destaque."""
    return re.sub(r"\*(.+?)\*", rf'<span style="font-family:{SERIF};font-style:italic;font-weight:400;color:{cor};'
                                rf'letter-spacing:0">\1</span>', esc(texto))


def registrar_fontes(c, project):
    """Copia as fontes do estilo para o projeto e declara @font-face (uma vez por composição)."""
    if getattr(c, "_fontes_cinema", False):
        return
    pasta = Path(__file__).resolve().parent.parent / "fonts"
    (Path(project) / "fonts").mkdir(parents=True, exist_ok=True)
    regras = ""
    for fam, arquivos in FONTES.items():
        for nome, peso in arquivos:
            if (pasta / nome).exists():
                shutil.copy2(pasta / nome, Path(project) / "fonts" / nome)
                estilo = "italic" if "Italic" in nome else "normal"
                regras += f'@font-face{{font-family:"{fam}";src:url("fonts/{nome}");font-weight:{peso};font-style:{estilo}}}'
    c.html.append(f"<style>{regras}</style>")
    c._fontes_cinema = True


def area(c):
    """Retângulo útil do painel: abaixo da divisória e acima da interface do Reels."""
    W, H = c.W, c.H
    return W * 0.07, H * 0.545, W * 0.86, H * 0.31


def _clip(c, i, ov, inner, z=6):
    x, y, w, h = area(c)
    c.clip(i, ov["start"], ov["duration"], f"left:{x:.0f}px;top:{y:.0f}px;width:{w:.0f}px;height:{h:.0f}px;z-index:{z}", inner)
    c.fade_out(f"#{i}", ov["start"] + ov["duration"], 0.2)


def glitch(c, sel, t, dur=0.45):
    """Glitch rápido: separação de cor (vermelho/ciano) e tremida horizontal."""
    passos = [(-6, 4), (5, -3), (-3, 2), (2, -1), (0, 0)]
    for k, (dx, sh) in enumerate(passos):
        ts = t + k * dur / len(passos)
        som = "none" if dx == 0 else f"{sh * 2}px 0 rgba(229,36,43,.85), {-sh * 2}px 0 rgba(0,220,255,.85)"
        c.tween(f'tl.set("{sel}",{{x:{dx},textShadow:"{som}"}},{ts:.3f});')


def svg_ambulancia(cor="#FFFFFF", cruz=VERMELHO, traco=3.2):
    """Ambulância em traço fino (estilo linha)."""
    return (f'<svg viewBox="0 0 124 84" width="100%" height="100%" fill="none" stroke="{cor}" stroke-width="{traco}" '
            f'stroke-linejoin="round" stroke-linecap="round">'
            f'<rect x="4" y="20" width="74" height="44" rx="6"/><path d="M78 32 h20 l18 17 v15 h-38"/>'
            f'<path d="M85 37 h11 l11 11 h-22 z"/><path d="M38 30 v24 M26 42 h24" stroke="{cruz}" stroke-width="{traco * 1.7}"/>'
            f'<path d="M16 20 v-7 h14 v7" stroke="{cruz}"/><circle cx="26" cy="66" r="9" fill="#05070D"/><circle cx="96" cy="66" r="9" fill="#05070D"/></svg>')


def alerta(c, ov):
    x, y, w, h = area(c)
    i = c.uid("al")
    ac = c.theme["accent"]
    tri = (f'<svg viewBox="0 0 100 90" width="{h * 0.26:.0f}" height="{h * 0.24:.0f}" fill="none" stroke="{ac}" stroke-width="5" '
           f'stroke-linejoin="round"><path d="M50 5 L95 85 H5 Z"/><path d="M50 32 v24" stroke-linecap="round"/><circle cx="50" cy="70" r="3.5" fill="{ac}"/></svg>')
    inner = (f'<div style="position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:{h * 0.05:.0f}px;text-align:center">'
             f'<div id="{i}-t">{tri}</div>'
             f'<div id="{i}-x" style="font-family:{SANS};font-weight:900;font-size:{h * 0.16:.0f}px;line-height:1.02;letter-spacing:-.02em;color:#fff">{rico(ov["texto"], ac)}</div>'
             f'<div id="{i}-s" style="font-family:{SANS};font-weight:600;font-size:{h * 0.058:.0f}px;color:rgba(255,255,255,.62);letter-spacing:.14em;text-transform:uppercase">{esc(ov.get("sub", ""))}</div></div>')
    _clip(c, i, ov, inner)
    s = ov["start"]
    c.tween(f'tl.fromTo("#{i}-t",{{scale:0,opacity:0}},{{scale:1,opacity:1,duration:.4,ease:"back.out(2.2)"}},{s:.3f});'
            f'tl.fromTo("#{i}-x",{{y:{h * 0.08:.0f},opacity:0,filter:"blur(12px)"}},{{y:0,opacity:1,filter:"blur(0px)",duration:.45,ease:"power3.out"}},{s + 0.15:.3f});'
            f'tl.fromTo("#{i}-s",{{opacity:0}},{{opacity:1,duration:.3}},{s + 0.5:.3f});')
    t = s + 0.8
    while t < s + ov["duration"] - 0.6:
        c.tween(f'tl.to("#{i}-t",{{opacity:.35,duration:.18}},{t:.3f});tl.to("#{i}-t",{{opacity:1,duration:.22}},{t + 0.18:.3f});')
        t += 1.0


def icones(c, ov):
    x, y, w, h = area(c)
    i = c.uid("ic")
    n = int(ov.get("n", 3))
    apagado = ov.get("apagado", False)
    lado = min(w / (n * 1.2), h * 0.55)
    cor = "rgba(255,255,255,.35)" if apagado else "#FFFFFF"
    cruz = "rgba(255,255,255,.35)" if apagado else VERMELHO
    itens = "".join(f'<div id="{i}-a{k}" style="width:{lado:.0f}px;height:{lado * 0.68:.0f}px">{svg_ambulancia(cor, cruz)}</div>' for k in range(n))
    ac = c.theme["accent"]
    inner = (f'<div style="position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:{h * 0.08:.0f}px">'
             f'<div style="display:flex;gap:{lado * 0.14:.0f}px;align-items:flex-end">{itens}</div>'
             f'<div id="{i}-l" style="font-family:{SANS};font-weight:900;letter-spacing:-.02em;text-align:center;line-height:1.05;'
             f'font-size:{h * (0.11 if len(ov.get("rotulo", "")) > 18 else 0.15):.0f}px;color:{"rgba(255,255,255,.75)" if apagado else "#fff"}">{rico(ov.get("rotulo", ""), ac)}</div></div>')
    _clip(c, i, ov, inner)
    s = ov["start"]
    for k in range(n):
        c.tween(f'tl.fromTo("#{i}-a{k}",{{y:{h * 0.08:.0f},opacity:0,filter:"blur(8px)"}},{{y:0,opacity:1,filter:"blur(0px)",duration:.4,ease:"power3.out"}},{s + 0.2 * k:.3f});')
    c.tween(f'tl.fromTo("#{i}-l",{{opacity:0,filter:"blur(10px)"}},{{opacity:1,filter:"blur(0px)",duration:.4}},{s + 0.2 * n:.3f});')


def carimbo(c, ov):
    x, y, w, h = area(c)
    i = c.uid("cb")
    fs = h * 0.17
    inner = (f'<div style="position:absolute;inset:0;display:flex;align-items:center;justify-content:center">'
             f'<div id="{i}-c" style="transform:rotate(-10deg);border:{fs * 0.07:.0f}px solid {VERMELHO};color:{VERMELHO};'
             f'font-family:{SANS};font-weight:900;font-size:{fs:.0f}px;letter-spacing:.08em;padding:{fs * 0.08:.0f}px {fs * 0.3:.0f}px;'
             f'border-radius:{fs * 0.08:.0f}px;background:rgba(5,7,13,.72)">{esc(ov["texto"])}</div></div>')
    _clip(c, i, ov, inner, z=8)
    for t in ov.get("batidas", [ov["start"]]):
        c.tween(f'tl.fromTo("#{i}-c",{{scale:2.2,opacity:0}},{{scale:1,opacity:1,duration:.2,ease:"power4.in"}},{t:.3f});')
        glitch(c, f"#{i}-c", t + 0.2)


def palavra(c, ov):
    x, y, w, h = area(c)
    i = c.uid("pw")
    ac = c.theme["accent"]
    seta = (f'<svg viewBox="0 0 160 40" width="{w * 0.42:.0f}" height="{h * 0.1:.0f}" fill="none" stroke="{VERMELHO}" stroke-width="3.5" '
            f'stroke-linecap="round" stroke-linejoin="round"><path d="M154 20 H8 M24 6 L8 20 L24 34"/></svg>')
    inner = (f'<div style="position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:{h * 0.04:.0f}px">'
             + (f'<div id="{i}-l" style="font-family:{SANS};font-weight:600;font-size:{h * 0.065:.0f}px;color:rgba(255,255,255,.7)">{esc(ov["apoio"])}</div>' if ov.get("apoio") else "")
             + f'<div id="{i}-p" style="font-family:{SERIF};font-style:italic;font-size:{h * 0.3:.0f}px;line-height:1;color:{ac}">{esc(ov["texto"])}</div>'
             f'<div id="{i}-a">{seta}</div></div>')
    _clip(c, i, ov, inner)
    s = ov["start"]
    if ov.get("apoio"):
        c.tween(f'tl.fromTo("#{i}-l",{{opacity:0}},{{opacity:1,duration:.3}},{s:.3f});')
    c.tween(f'tl.fromTo("#{i}-p",{{opacity:0,filter:"blur(14px)",scale:1.08}},{{opacity:1,filter:"blur(0px)",scale:1,duration:.5,ease:"power3.out"}},{s + 0.1:.3f});'
            f'tl.fromTo("#{i}-a",{{x:{w * 0.25:.0f},opacity:0}},{{x:0,opacity:1,duration:.5,ease:"power3.out"}},{s + 0.35:.3f});')


def lista_x(c, ov):
    x, y, w, h = area(c)
    i = c.uid("lx")
    itens = ov["itens"]
    fs = h * 0.135
    ac = c.theme["accent"]
    linhas = "".join(
        f'<div id="{i}-r{k}" style="display:flex;align-items:center;gap:{fs * 0.55:.0f}px;opacity:0">'
        f'<svg viewBox="0 0 40 40" width="{fs * 1.1:.0f}" height="{fs * 1.1:.0f}" fill="none" stroke="{VERMELHO}" stroke-width="3" stroke-linecap="round">'
        f'<circle cx="20" cy="20" r="17"/><path d="M13 13 L27 27 M27 13 L13 27"/></svg>'
        f'<div style="font-family:{SANS};font-weight:900;font-size:{fs:.0f}px;letter-spacing:-.02em;color:#fff;line-height:1.05">{rico(it["texto"], ac)}</div></div>'
        for k, it in enumerate(itens))
    inner = (f'<div style="position:absolute;inset:0;display:flex;flex-direction:column;justify-content:center;gap:{h * 0.11:.0f}px;padding-left:{w * 0.05:.0f}px">{linhas}</div>')
    _clip(c, i, ov, inner)
    for k, it in enumerate(itens):
        t = it.get("inicio", ov["start"] + 0.5 * k)
        c.tween(f'tl.fromTo("#{i}-r{k}",{{x:{-w * 0.08:.0f},opacity:0,filter:"blur(10px)"}},{{x:0,opacity:1,filter:"blur(0px)",duration:.4,ease:"power3.out"}},{t:.3f});')


def tentativas(c, ov):
    x, y, w, h = area(c)
    i = c.uid("tt")
    n = int(ov.get("n", 4))
    d = min(w / (n * 1.5), h * 0.3)
    ac = c.theme["accent"]
    circ = "".join(
        f'<div style="position:relative;width:{d:.0f}px;height:{d:.0f}px">'
        f'<div id="{i}-c{k}" style="position:absolute;inset:0;border-radius:50%;border:{max(2, d * 0.03):.0f}px solid rgba(255,255,255,.85);display:flex;align-items:center;'
        f'justify-content:center;font-family:{SANS};font-weight:600;font-size:{d * 0.3:.0f}px;color:#fff">{k + 1}ª</div>'
        f'<svg id="{i}-x{k}" viewBox="0 0 40 40" style="position:absolute;inset:-{d * 0.1:.0f}px;width:{d * 1.2:.0f}px;height:{d * 1.2:.0f}px;opacity:0" '
        f'fill="none" stroke="{VERMELHO}" stroke-width="3.2" stroke-linecap="round"><path d="M9 9 L31 31 M31 9 L9 31"/></svg></div>'
        for k in range(n))
    inner = (f'<div style="position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:{h * 0.06:.0f}px">'
             f'<div style="display:flex;gap:{d * 0.45:.0f}px">{circ}</div>'
             f'<div id="{i}-r" style="font-family:{SANS};font-weight:900;font-size:{h * 0.22:.0f}px;line-height:1;letter-spacing:-.02em;color:#fff;opacity:0">{rico(ov.get("rotulo", ""), ac)}</div>'
             f'<div id="{i}-s" style="font-family:{SANS};font-weight:600;font-size:{h * 0.06:.0f}px;letter-spacing:.16em;color:rgba(255,255,255,.65);opacity:0">{esc(ov.get("sub", ""))}</div></div>')
    _clip(c, i, ov, inner)
    s = ov["start"]
    for k in range(n):
        c.tween(f'tl.fromTo("#{i}-c{k}",{{scale:.4,opacity:0}},{{scale:1,opacity:1,duration:.3,ease:"back.out(2)"}},{s + 0.12 * k:.3f});')
    for k, t in enumerate(ov.get("marcas", [])):
        c.tween(f'tl.fromTo("#{i}-x{k}",{{scale:1.8,opacity:0}},{{scale:1,opacity:1,duration:.18,ease:"power4.in"}},{t:.3f});'
                f'tl.to("#{i}-c{k}",{{opacity:.35,duration:.2}},{t + 0.18:.3f});')
    if ov.get("rotulo_em"):
        c.tween(f'tl.fromTo("#{i}-r",{{opacity:0,scale:.8}},{{opacity:1,scale:1,duration:.3,ease:"back.out(2)"}},{ov["rotulo_em"]:.3f});')
        glitch(c, f"#{i}-r", ov["rotulo_em"] + 0.3)
    if ov.get("sub_em"):
        c.tween(f'tl.fromTo("#{i}-s",{{y:16,opacity:0}},{{y:0,opacity:1,duration:.3}},{ov["sub_em"]:.3f});')


def faixas(c, ov):
    """Frases de fechamento: grotesca + *serifada itálica*, com um fio na cor de destaque crescendo embaixo."""
    x, y, w, h = area(c)
    i = c.uid("fx")
    itens = ov["itens"]
    fs = h * 0.13
    ac = c.theme["accent"]
    linhas = "".join(
        f'<div id="{i}-f{k}" style="align-self:{"flex-start" if k % 2 == 0 else "flex-end"};text-align:{"left" if k % 2 == 0 else "right"};opacity:0">'
        f'<div style="font-family:{SANS};font-weight:900;font-size:{fs:.0f}px;letter-spacing:-.02em;line-height:1.05;color:#fff">{rico(it["texto"], ac)}</div>'
        f'<div id="{i}-u{k}" style="height:{max(3, h * 0.01):.0f}px;background:{ac};margin-top:{fs * 0.18:.0f}px;transform-origin:{"left" if k % 2 == 0 else "right"};transform:scaleX(0)"></div></div>'
        for k, it in enumerate(itens))
    inner = f'<div style="position:absolute;inset:0;display:flex;flex-direction:column;justify-content:center;gap:{h * 0.14:.0f}px">{linhas}</div>'
    _clip(c, i, ov, inner)
    for k, it in enumerate(itens):
        t = it.get("inicio", ov["start"] + 0.6 * k)
        dx = -w * 0.1 if k % 2 == 0 else w * 0.1
        c.tween(f'tl.fromTo("#{i}-f{k}",{{x:{dx:.0f},opacity:0,filter:"blur(10px)"}},{{x:0,opacity:1,filter:"blur(0px)",duration:.45,ease:"power3.out"}},{t:.3f});'
                f'tl.to("#{i}-u{k}",{{scaleX:1,duration:.5,ease:"power2.out"}},{t + 0.3:.3f});')


TIPOS = {"alerta": alerta, "icones": icones, "carimbo": carimbo, "palavra": palavra,
         "lista_x": lista_x, "tentativas": tentativas, "faixas": faixas}


def painel_fundo(c, dur, project):
    """Fundo do painel (quase preto, toque de azul) + sombra no pé do vídeo de cima para a legenda ficar legível."""
    W, H = c.W, c.H
    registrar_fontes(c, project)
    inner = (f'<div style="position:absolute;left:0;top:{H * 0.30:.0f}px;width:{W}px;height:{H * 0.20 + 2:.0f}px;'
             f'background:linear-gradient(180deg,rgba(0,0,0,0) 0%,rgba(0,0,0,.62) 100%)"></div>'
             f'<div id="painel" style="position:absolute;left:0;top:{H * 0.5:.0f}px;width:{W}px;height:{H * 0.5:.0f}px;'
             f'background:radial-gradient(ellipse at 50% 30%, #121B33 0%, #070A14 60%, #04050A 100%)"></div>')
    c.clip("painelclip", 0, dur, "left:0;top:0;width:100%;height:100%;z-index:2", inner)


def legenda_camadas(c, words, opts, theme, project):
    """Legenda em duas camadas (referência "vídeo um"): apoio pequeno e mais leve + palavras principais grandes.
    Cada palavra entra desfocada e fica nítida quando é falada. Fica no pé do vídeo de cima (acima da divisória)."""
    from build_ass import group_words, is_emphasis
    registrar_fontes(c, project)
    W, H = c.W, c.H
    ac = theme["accent"]
    base_y = opts.get("pos_y", 0.445) * H                    # linha de baixo da legenda (acima da divisória)
    grande, pequeno = H * opts.get("tam_grande", 0.047), H * opts.get("tam_pequeno", 0.024)
    grupos = group_words(words, opts.get("max_words", 6), max_chars=opts.get("max_chars", 34))
    for gi, g in enumerate(grupos):
        ini = g[0]["start"]
        fim = g[-1]["end"] + 0.25
        if gi + 1 < len(grupos):
            fim = min(fim, grupos[gi + 1][0]["start"])
        fim = max(fim, ini + 0.3)
        n_grande = 1 if len(g) <= 2 else 2
        if len(g) > 2 and len(g[-1]["word"]) <= 3:            # "de", "o"... não fica sozinho na linha grande
            n_grande = 3 if len(g) > 3 else 2
        apoio, princ = g[:-n_grande] if len(g) > n_grande else [], g[-n_grande:]
        chave = max(range(len(princ)), key=lambda k: (is_emphasis(princ[k]["word"], opts), len(princ[k]["word"].strip(".,!?"))))
        i = c.uid("lc")
        span = lambda w, k, cor="": f'<span id="{i}-w{k}" style="display:inline-block;{cor}">{esc(w["word"])}</span>'
        linha1 = " ".join(span(w, k) for k, w in enumerate(apoio))
        linha2 = " ".join(span(w, len(apoio) + k, f"color:{ac}" if k == chave else "") for k, w in enumerate(princ))
        inner = (f'<div style="position:absolute;left:7%;width:86%;bottom:{H - base_y:.0f}px;text-align:center;'
                 f'text-shadow:0 3px 18px rgba(0,0,0,.55)">'
                 + (f'<div style="font-family:{SANS};font-weight:600;font-size:{pequeno:.0f}px;line-height:1.2;color:rgba(255,255,255,.82);'
                    f'margin-bottom:{pequeno * 0.25:.0f}px">{linha1}</div>' if apoio else "")
                 + f'<div style="font-family:{SANS};font-weight:900;font-size:{grande:.0f}px;line-height:1.02;letter-spacing:-.025em;color:#fff">{linha2}</div></div>')
        c.clip(i, ini, fim - ini, "left:0;top:0;width:100%;height:100%;z-index:10", inner)
        for k, w in enumerate(g):
            t = max(ini, w["start"] - 0.04)
            c.tween(f'tl.fromTo("#{i}-w{k}",{{opacity:0,filter:"blur(10px)",y:{grande * 0.12:.0f}}},'
                    f'{{opacity:1,filter:"blur(0px)",y:0,duration:.22,ease:"power2.out"}},{t:.3f});')


def cartao_final(c, ov, project):
    """Cartão final do estilo cinema: fundo (preto por padrão), "Siga" na grotesca e *@perfil* em serifada itálica."""
    registrar_fontes(c, project)
    W, H = c.W, c.H
    i = c.uid("cf")
    ac = c.theme["accent"]
    s, d = ov["start"], ov["duration"]
    inner = (f'<div style="position:absolute;inset:0;background:{ov.get("background", "#000")}"></div>'
             f'<div style="position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:{H * 0.022:.0f}px;text-align:center">'
             f'<div id="{i}-t" style="font-family:{SANS};font-weight:900;font-size:{H * 0.05:.0f}px;letter-spacing:-.02em;line-height:1.05;color:#fff">{rico(ov.get("text", ""), ac)}</div>'
             f'<div id="{i}-b" style="width:{W * 0.12:.0f}px;height:{max(3, H * 0.0025):.0f}px;background:{ac};transform:scaleX(0)"></div>'
             f'<div id="{i}-s" style="font-family:{SANS};font-weight:600;font-size:{H * 0.016:.0f}px;letter-spacing:.24em;color:rgba(255,255,255,.7)">{esc(ov.get("subtext", ""))}</div></div>')
    c.clip(i, s, d, "left:0;top:0;width:100%;height:100%;z-index:14", inner)
    c.tween(f'tl.fromTo("#{i}",{{opacity:0}},{{opacity:1,duration:.25}},{s:.3f});'
            f'tl.fromTo("#{i}-t",{{opacity:0,filter:"blur(14px)",y:20}},{{opacity:1,filter:"blur(0px)",y:0,duration:.5,ease:"power3.out"}},{s + 0.1:.3f});'
            f'tl.to("#{i}-b",{{scaleX:1,duration:.45,ease:"power2.out"}},{s + 0.45:.3f});'
            f'tl.fromTo("#{i}-s",{{opacity:0}},{{opacity:1,duration:.35}},{s + 0.6:.3f});')
