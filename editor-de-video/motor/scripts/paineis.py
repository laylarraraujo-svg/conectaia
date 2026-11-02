"""Animações do painel inferior da tela dividida (formato "dividido").

Cada função recebe a composição (Comp do hf_project) e o overlay do plano. Tudo é desenhado dentro da área
segura do painel de baixo (entre a legenda, no meio da tela, e a interface do Instagram, no rodapé).

Tipos: alerta, icones, carimbo, palavra, lista_x, tentativas, faixas.
"""
import html
import re

VERMELHO = "#E5242B"


def esc(s):
    return html.escape(str(s), quote=True)


def destaque(texto, cor):
    return re.sub(r"\*(.+?)\*", rf'<span style="color:{cor}">\1</span>', esc(texto))


def area(c):
    """Retângulo útil do painel: abaixo da legenda e acima da interface do Reels."""
    W, H = c.W, c.H
    return W * 0.07, H * 0.575, W * 0.86, H * 0.285      # x, y, largura, altura


def _clip(c, i, ov, inner, z=6):
    x, y, w, h = area(c)
    c.clip(i, ov["start"], ov["duration"], f"left:{x:.0f}px;top:{y:.0f}px;width:{w:.0f}px;height:{h:.0f}px;z-index:{z}", inner)
    c.fade_out(f"#{i}", ov["start"] + ov["duration"], 0.2)


def svg_ambulancia(cor="#FFFFFF", cruz=VERMELHO):
    return (f'<svg viewBox="0 0 120 80" width="100%" height="100%">'
            f'<rect x="4" y="18" width="74" height="44" rx="5" fill="{cor}"/>'
            f'<path d="M78 30 h20 l16 16 v16 h-36 z" fill="{cor}"/>'
            f'<path d="M84 34 h12 l10 11 h-22 z" fill="#9CC3E6"/>'
            f'<rect x="34" y="27" width="8" height="26" fill="{cruz}"/><rect x="25" y="36" width="26" height="8" fill="{cruz}"/>'
            f'<rect x="14" y="11" width="16" height="7" rx="2" fill="{cruz}"/>'
            f'<circle cx="26" cy="64" r="10" fill="#1d1d1d"/><circle cx="26" cy="64" r="4" fill="#bbb"/>'
            f'<circle cx="94" cy="64" r="10" fill="#1d1d1d"/><circle cx="94" cy="64" r="4" fill="#bbb"/></svg>')


def alerta(c, ov):
    x, y, w, h = area(c)
    i = c.uid("al")
    ac = c.theme["accent"]
    tri = (f'<svg viewBox="0 0 100 90" width="{h * 0.36:.0f}" height="{h * 0.33:.0f}"><path d="M50 4 L96 86 H4 Z" fill="{ac}" '
           f'stroke="#111" stroke-width="4" stroke-linejoin="round"/><rect x="45" y="30" width="10" height="32" rx="3" fill="#111"/>'
           f'<circle cx="50" cy="73" r="6" fill="#111"/></svg>')
    inner = (f'<div style="position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:{h * 0.05:.0f}px;text-align:center">'
             f'<div id="{i}-t">{tri}</div>'
             f'<div id="{i}-x" style="font-family:Montserrat,sans-serif;font-weight:800;font-size:{h * 0.17:.0f}px;line-height:1.05;color:#fff;text-transform:uppercase">{destaque(ov["texto"], ac)}</div>'
             f'<div id="{i}-s" style="font-family:Montserrat,sans-serif;font-weight:700;font-size:{h * 0.075:.0f}px;color:#C9D3EA;letter-spacing:.04em">{esc(ov.get("sub", ""))}</div></div>')
    _clip(c, i, ov, inner)
    s = ov["start"]
    c.tween(f'tl.fromTo("#{i}-t",{{scale:0,rotation:-20}},{{scale:1,rotation:0,duration:.45,ease:"back.out(2.5)"}},{s:.3f});'
            f'tl.fromTo("#{i}-x",{{y:{h * 0.15:.0f},opacity:0}},{{y:0,opacity:1,duration:.35,ease:"power3.out"}},{s + 0.2:.3f});'
            f'tl.fromTo("#{i}-s",{{opacity:0}},{{opacity:1,duration:.3}},{s + 0.45:.3f});')
    t = s + 0.7
    while t < s + ov["duration"] - 0.6:                     # pisca: pulso a cada 0,9 s
        c.tween(f'tl.to("#{i}-t",{{scale:1.15,duration:.2,ease:"power2.out"}},{t:.3f});tl.to("#{i}-t",{{scale:1,duration:.25}},{t + 0.2:.3f});')
        t += 0.9


def icones(c, ov):
    x, y, w, h = area(c)
    i = c.uid("ic")
    n = int(ov.get("n", 3))
    apagado = ov.get("apagado", False)
    lado = min(w / (n * 1.15), h * 0.62)
    cor = "#7C8496" if apagado else "#FFFFFF"
    cruz = "#5A6070" if apagado else VERMELHO
    itens = "".join(f'<div id="{i}-a{k}" style="width:{lado:.0f}px;height:{lado * 0.67:.0f}px">{svg_ambulancia(cor, cruz)}</div>' for k in range(n))
    inner = (f'<div style="position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:{h * 0.07:.0f}px">'
             f'<div style="display:flex;gap:{lado * 0.12:.0f}px;align-items:flex-end">{itens}</div>'
             f'<div id="{i}-l" style="font-family:Montserrat,sans-serif;font-weight:800;font-size:{h * (0.105 if len(ov.get("rotulo", "")) > 18 else 0.14):.0f}px;'
             f'text-align:center;line-height:1.1;text-transform:uppercase;color:{"#C9D3EA" if apagado else c.theme["accent"]}">{destaque(ov.get("rotulo", ""), c.theme["accent"])}</div></div>')
    _clip(c, i, ov, inner)
    s = ov["start"]
    for k in range(n):
        ent = "{x:-60,opacity:0}" if apagado else "{x:" + f"{-w:.0f}" + ",opacity:0}"
        c.tween(f'tl.fromTo("#{i}-a{k}",{ent},{{x:0,opacity:1,duration:.45,ease:"power3.out"}},{s + 0.25 * k:.3f});')
    c.tween(f'tl.fromTo("#{i}-l",{{scale:.6,opacity:0}},{{scale:1,opacity:1,duration:.35,ease:"back.out(2)"}},{s + 0.25 * n:.3f});')


def carimbo(c, ov):
    x, y, w, h = area(c)
    i = c.uid("cb")
    fs = h * 0.2
    inner = (f'<div style="position:absolute;inset:0;display:flex;align-items:center;justify-content:center">'
             f'<div id="{i}-c" style="transform:rotate(-12deg);border:{fs * 0.1:.0f}px solid {VERMELHO};color:{VERMELHO};'
             f'font-family:Montserrat,sans-serif;font-weight:800;font-size:{fs:.0f}px;letter-spacing:.06em;padding:{fs * 0.1:.0f}px {fs * 0.35:.0f}px;'
             f'border-radius:{fs * 0.12:.0f}px;background:rgba(255,255,255,.08);text-shadow:0 0 1px {VERMELHO}">{esc(ov["texto"])}</div></div>')
    _clip(c, i, ov, inner, z=8)
    for t in ov.get("batidas", [ov["start"]]):
        c.tween(f'tl.fromTo("#{i}-c",{{scale:2.4,opacity:0}},{{scale:1,opacity:1,duration:.22,ease:"power4.in"}},{t:.3f});')
        c.tween(f'tl.fromTo("#painel",{{x:0}},{{x:14,duration:.05,yoyo:true,repeat:5,ease:"none"}},{t + 0.22:.3f});'
                f'tl.set("#painel",{{x:0}},{t + 0.55:.3f});')


def palavra(c, ov):
    x, y, w, h = area(c)
    i = c.uid("pw")
    ac = c.theme["accent"]
    seta = (f'<svg viewBox="0 0 120 60" width="{h * 0.5:.0f}" height="{h * 0.25:.0f}"><path d="M50 8 L8 30 L50 52 V38 H112 V22 H50 Z" fill="{VERMELHO}"/></svg>')
    inner = (f'<div style="position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:{h * 0.06:.0f}px">'
             f'<div id="{i}-a">{seta}</div>'
             f'<div id="{i}-p" style="font-family:Montserrat,sans-serif;font-weight:800;font-size:{h * 0.24:.0f}px;color:{ac};text-transform:uppercase;'
             f'letter-spacing:.02em">{esc(ov["texto"])}</div></div>')
    _clip(c, i, ov, inner)
    s = ov["start"]
    c.tween(f'tl.fromTo("#{i}-p",{{scale:.5,opacity:0}},{{scale:1,opacity:1,duration:.35,ease:"back.out(2)"}},{s:.3f});'
            f'tl.fromTo("#{i}-a",{{x:{w * 0.3:.0f},opacity:0}},{{x:0,opacity:1,duration:.4,ease:"power3.out"}},{s + 0.15:.3f});'
            f'tl.to("#{i}-a",{{x:-{w * 0.12:.0f},duration:.6,yoyo:true,repeat:{max(1, int(ov["duration"] / 0.6) - 2)},ease:"sine.inOut"}},{s + 0.55:.3f});')


def lista_x(c, ov):
    x, y, w, h = area(c)
    i = c.uid("lx")
    itens = ov["itens"]
    fs = h * 0.15
    linhas = "".join(
        f'<div id="{i}-r{k}" style="display:flex;align-items:center;gap:{fs * 0.5:.0f}px;opacity:0">'
        f'<div style="flex:none;width:{fs * 1.3:.0f}px;height:{fs * 1.3:.0f}px;border-radius:50%;background:{VERMELHO};display:flex;align-items:center;'
        f'justify-content:center;color:#fff;font-family:Montserrat,sans-serif;font-weight:800;font-size:{fs * 0.9:.0f}px">✕</div>'
        f'<div style="font-family:Montserrat,sans-serif;font-weight:800;font-size:{fs:.0f}px;color:#fff;text-transform:uppercase;line-height:1.05">'
        f'{destaque(it["texto"], c.theme["accent"])}</div></div>' for k, it in enumerate(itens))
    inner = (f'<div style="position:absolute;inset:0;display:flex;flex-direction:column;justify-content:center;gap:{h * 0.12:.0f}px;padding-left:{w * 0.04:.0f}px">{linhas}</div>')
    _clip(c, i, ov, inner)
    for k, it in enumerate(itens):
        t = it.get("inicio", ov["start"] + 0.5 * k)
        c.tween(f'tl.fromTo("#{i}-r{k}",{{x:{-w * 0.25:.0f},opacity:0}},{{x:0,opacity:1,duration:.35,ease:"back.out(1.6)"}},{t:.3f});')


def tentativas(c, ov):
    x, y, w, h = area(c)
    i = c.uid("tt")
    n = int(ov.get("n", 4))
    d = min(w / (n * 1.45), h * 0.34)
    circ = "".join(
        f'<div style="position:relative;width:{d:.0f}px;height:{d:.0f}px">'
        f'<div id="{i}-c{k}" style="position:absolute;inset:0;border-radius:50%;border:{d * 0.06:.0f}px solid #fff;display:flex;align-items:center;justify-content:center;'
        f'font-family:Montserrat,sans-serif;font-weight:800;font-size:{d * 0.32:.0f}px;color:#fff">{k + 1}ª</div>'
        f'<div id="{i}-x{k}" style="position:absolute;inset:-{d * 0.08:.0f}px;display:flex;align-items:center;justify-content:center;'
        f'font-family:Montserrat,sans-serif;font-weight:800;font-size:{d * 1.05:.0f}px;line-height:1;color:{VERMELHO};opacity:0">✕</div></div>'
        for k in range(n))
    inner = (f'<div style="position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:{h * 0.06:.0f}px">'
             f'<div style="display:flex;gap:{d * 0.4:.0f}px">{circ}</div>'
             f'<div id="{i}-r" style="font-family:Montserrat,sans-serif;font-weight:800;font-size:{h * 0.2:.0f}px;line-height:1;color:{c.theme["accent"]};opacity:0">{esc(ov.get("rotulo", ""))}</div>'
             f'<div id="{i}-s" style="font-family:Montserrat,sans-serif;font-weight:800;font-size:{h * 0.085:.0f}px;letter-spacing:.06em;color:#fff;opacity:0">{esc(ov.get("sub", ""))}</div></div>')
    _clip(c, i, ov, inner)
    s = ov["start"]
    for k in range(n):
        c.tween(f'tl.fromTo("#{i}-c{k}",{{scale:0}},{{scale:1,duration:.3,ease:"back.out(2)"}},{s + 0.12 * k:.3f});')
    for k, t in enumerate(ov.get("marcas", [])):
        c.tween(f'tl.fromTo("#{i}-x{k}",{{scale:2,opacity:0}},{{scale:1,opacity:1,duration:.2,ease:"power4.in"}},{t:.3f});'
                f'tl.to("#{i}-c{k}",{{opacity:.45,duration:.2}},{t + 0.2:.3f});')
    if ov.get("rotulo_em"):
        c.tween(f'tl.fromTo("#{i}-r",{{scale:.4,opacity:0}},{{scale:1,opacity:1,duration:.35,ease:"back.out(2.2)"}},{ov["rotulo_em"]:.3f});')
    if ov.get("sub_em"):
        c.tween(f'tl.fromTo("#{i}-s",{{y:20,opacity:0}},{{y:0,opacity:1,duration:.3}},{ov["sub_em"]:.3f});')


def faixas(c, ov):
    x, y, w, h = area(c)
    i = c.uid("fx")
    itens = ov["itens"]
    fs = h * 0.125
    linhas = "".join(
        f'<div id="{i}-f{k}" style="align-self:{"flex-start" if k % 2 == 0 else "flex-end"};transform:skewX(-8deg);'
        f'background:{c.theme["accent"] if k % 2 == 0 else "#fff"};color:#111;padding:{fs * 0.35:.0f}px {fs * 0.6:.0f}px;opacity:0;'
        f'font-family:Montserrat,sans-serif;font-weight:800;font-size:{fs:.0f}px;line-height:1.05;text-transform:uppercase;max-width:96%">'
        f'{esc(it["texto"])}</div>' for k, it in enumerate(itens))
    inner = f'<div style="position:absolute;inset:0;display:flex;flex-direction:column;justify-content:center;gap:{h * 0.1:.0f}px">{linhas}</div>'
    _clip(c, i, ov, inner)
    for k, it in enumerate(itens):
        dx = -w if k % 2 == 0 else w
        t = it.get("inicio", ov["start"] + 0.6 * k)
        c.tween(f'tl.fromTo("#{i}-f{k}",{{x:{dx:.0f},opacity:0}},{{x:0,opacity:1,duration:.4,ease:"power3.out"}},{t:.3f});')


TIPOS = {"alerta": alerta, "icones": icones, "carimbo": carimbo, "palavra": palavra,
         "lista_x": lista_x, "tentativas": tentativas, "faixas": faixas}


def painel_fundo(c, dur):
    """Fundo do painel de baixo, na cor da marca, cobrindo toda a duração (também esconde o zoom da metade de cima)."""
    W, H = c.W, c.H
    cor = c.theme.get("brand", "#002776")
    inner = (f'<div id="painel" style="position:absolute;left:0;top:{H * 0.5:.0f}px;width:{W}px;height:{H * 0.5:.0f}px;'
             f'background:radial-gradient(ellipse at 50% 35%, {cor} 0%, #00123A 100%)">'
             f'<div style="position:absolute;left:0;top:0;width:100%;height:{max(6, H * 0.004):.0f}px;background:{c.theme["accent"]}"></div></div>')
    c.clip("painelclip", 0, dur, f"left:0;top:0;width:100%;height:100%;z-index:2", inner)
