#!/usr/bin/env python3
"""Gera um projeto HyperFrames (HTML + GSAP) com legendas, títulos e gráficos animados e renderiza em MP4.

O HyperFrames abre a composição em um Chrome headless, avança quadro a quadro e codifica com FFmpeg.
Aqui montamos a composição a partir do transcript e do spec; o vídeo de fundo é o vídeo já cortado.

Uso isolado:
  python hf_project.py base.mp4 --transcript t.json --spec edicao.json -o saida.mp4 [--preset padrao]
"""
import argparse
import html
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from build_ass import DEFAULT_THEME, SUB_PRESETS, group_words, is_emphasis
from common import local_font, pick_font, probe, punch_schedule

HF_VERSION = os.environ.get("HYPERFRAMES_VERSION", "0.8.209")   # versão testada; sobrescreva se quiser
GSAP_VERSION = "3.14.2"

CSS = """
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:@W@px;height:@H@px;overflow:hidden;background:#000}
body{font-family:@FONT_STACK@}
#root{position:absolute;inset:0;overflow:hidden}
#a-roll{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;z-index:0}
.abs{position:absolute}
.cap{position:absolute;left:0;width:100%;height:0;display:flex;align-items:center;justify-content:center;z-index:10}
.cap-in{font-size:@CAP_SIZE@px;text-align:center;white-space:nowrap;color:@TEXT@;line-height:1.12;font-weight:@CAP_WEIGHT@;font-style:@CAP_STYLE@;
  text-shadow:0 @SHADOW_Y@px @SHADOW_B@px rgba(0,0,0,.62)}
.cap-in .l2{color:@ACCENT@;font-size:1.15em;text-transform:uppercase}
.cap-in .k{color:@ACCENT@}
.cap-viral{text-transform:uppercase;font-weight:800;-webkit-text-stroke:@STROKE@px #000;paint-order:stroke fill;text-shadow:0 6px 0 rgba(0,0,0,.55)}
.cap-box{background:rgba(11,11,16,.78);padding:.18em .5em;border-radius:.3em;text-shadow:none}
.ttl{position:absolute;left:0;width:100%;text-align:center;color:@TEXT@;font-weight:700;z-index:12;
  text-shadow:0 @SHADOW_Y@px @SHADOW_B@px rgba(0,0,0,.55);padding:0 8%}
.ttl em{font-style:normal;color:@ACCENT@}
.num{position:absolute;left:0;width:100%;display:flex;justify-content:center;align-items:baseline;gap:.35em;z-index:12;
  color:@TEXT@;font-weight:800;text-transform:uppercase;text-shadow:0 @SHADOW_Y@px @SHADOW_B@px rgba(0,0,0,.6)}
.num b{color:@ACCENT@;font-weight:800}
.lt{position:absolute;z-index:11;background:rgba(11,11,16,.82);border-left:@BAR@px solid @ACCENT@;color:@TEXT@}
.lt .t{font-weight:700}.lt .s{color:#D1D5DB;font-weight:500}
.card{position:absolute;z-index:9;background:rgba(11,11,16,.9);color:@TEXT@;overflow:hidden}
.card .ct{position:absolute;font-weight:700}
.bar{position:absolute;bottom:0;border-radius:8px 8px 0 0}
.val{position:absolute;left:50%;transform:translateX(-50%);white-space:nowrap;font-weight:700;color:@TEXT@}
.lab{position:absolute;white-space:nowrap;text-align:center;color:@TEXT@}
.ring{position:absolute;border-radius:50%}
.sq{position:absolute;border:@DASH@px dashed @ACCENT@;background:rgba(11,11,16,.86);border-radius:18%;
  display:flex;align-items:center;justify-content:center;color:@TEXT@;font-weight:700;text-align:center}
.full{position:absolute;inset:0;z-index:7;background:linear-gradient(180deg,#0A0A0F,#1E1E28);color:@TEXT@}
"""


FULL = "left:0;top:0;width:100%;height:100%;pointer-events:none"   # o .clip do HyperFrames dá caixa de quadro inteiro


def esc(s):
    return html.escape(str(s), quote=True)


def fmt_js(v, dec=0, pre="", suf=""):
    return json.dumps({"dec": dec, "pre": pre, "suf": suf})


def box_pos(position, w, h, W, H):
    """Retorna (left, top) em px conforme o nome da posição."""
    table = {
        "top": ((W - w) / 2, 0.07 * H), "center": ((W - w) / 2, (H - h) / 2), "bottom": ((W - w) / 2, 0.62 * H),
        "top-left": (0.04 * W, 0.07 * H), "top-right": (W - w - 0.04 * W, 0.07 * H),
        "bottom-left": (0.04 * W, H - h - 0.10 * H), "bottom-right": (W - w - 0.04 * W, H - h - 0.10 * H),
        "full": (0, 0),
    }
    return table.get(position, table["top"])


def visual_size(kind, W, H):
    v = W < H
    if kind == "pillars":
        return W, H
    if kind == "steps":
        return 0.74 * W, 0.13 * H
    if kind == "cards":
        return 0.92 * W, 0.16 * H
    if kind == "stat":
        return (0.62 * W, 0.15 * H) if v else (0.28 * W, 0.24 * H)
    return (0.88 * W, 0.27 * H) if v else (0.44 * W, 0.44 * H)


class Comp:
    """Acumula HTML e instruções GSAP da composição."""

    def __init__(self, W, H, theme):
        self.W, self.H, self.theme = W, H, theme
        self.html, self.js, self.n = [], [], 0

    def uid(self, p="e"):
        self.n += 1
        return f"{p}{self.n}"

    def clip(self, i, start, dur, style, inner, cls=""):
        self.html.append(f'<div id="{i}" class="clip {cls}" data-start="{start:.3f}" data-duration="{max(dur, 0.1):.3f}" '
                         f'style="{style}">{inner}</div>')

    def tween(self, line):
        self.js.append(line)

    def fade_out(self, sel, end, d=0.25):
        self.js.append(f'tl.to("{sel}",{{opacity:0,duration:{d},ease:"power1.in"}},{max(end - d, 0):.3f});')


# --------------------------------------------------------------------------- legendas
def build_captions(c, words, opts, theme, base_px):
    W, H = c.W, c.H
    style = opts.get("style", "ref")
    preset = {**SUB_PRESETS.get(style, SUB_PRESETS["ref"])}
    if opts.get("max_words"):
        preset["max_words"] = opts["max_words"]
    vertical = W < H
    pos_y = opts.get("pos_y", preset.get("pos_y", 0.76 if vertical else 0.88))
    groups = group_words(words, preset["max_words"], max_chars=opts.get("max_chars", preset.get("max_chars", 22 if vertical else 42)))
    for gi, g in enumerate(groups):
        start = g[0]["start"]
        end = g[-1]["end"] + 0.2
        if gi + 1 < len(groups):
            end = min(end, groups[gi + 1][0]["start"])
        end = max(end, start + 0.15)
        i = c.uid("cap")
        cls = "cap-in" + (" cap-viral" if style == "viral" else " cap-box" if style == "box" else "")
        if preset.get("stack"):
            ws = [(w["word"].strip("*"), is_emphasis(w["word"], opts)) for w in g]
            k = len(ws)
            while k > 0 and ws[k - 1][1]:
                k -= 1
            plain, key = ws[:k], ws[k:]
            if key and plain:
                inner = f'<div class="l1">{esc(" ".join(t for t, _ in plain))}</div><div class="l2">{esc(" ".join(t for t, _ in key))}</div>'
            elif key:
                inner = f'<div class="l2">{esc(" ".join(t for t, _ in key))}</div>'
            else:
                inner = '<div class="l1">' + " ".join(f'<span class="k">{esc(t)}</span>' if e else esc(t) for t, e in ws) + "</div>"
            c.clip(i, start, end - start, FULL, f'<div class="cap" style="top:{pos_y * 100:.1f}%"><div id="{i}-in" class="{cls}">{inner}</div></div>')
        else:
            spans = "".join(f'<span id="{i}-w{j}">{esc(w["word"])}</span> ' for j, w in enumerate(g))
            c.clip(i, start, end - start, FULL, f'<div class="cap" style="top:{pos_y * 100:.1f}%"><div id="{i}-in" class="{cls}">{spans.strip()}</div></div>')
            if preset.get("highlight"):
                for j, w in enumerate(g):
                    nxt = g[j + 1]["start"] if j + 1 < len(g) else end
                    c.tween(f'tl.set("#{i}-w{j}",{{color:"{theme["accent"]}"}},{w["start"]:.3f});'
                            f'tl.set("#{i}-w{j}",{{color:"{theme["text"]}"}},{nxt:.3f});')
        c.tween(f'tl.fromTo("#{i}-in",{{scale:.85,opacity:0}},{{scale:1,opacity:1,duration:.12,ease:"power2.out"}},{start:.3f});')


# --------------------------------------------------------------------------- overlays de texto
def build_title(c, ov, base):
    H = c.H
    pos = ov.get("position", "top")
    y = {"top": 0.13, "center": 0.5, "bottom": 0.78}.get(pos, 0.13) * H
    i = c.uid("ttl")
    text = esc(ov["text"])
    text = re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)
    size = int(0.062 * H)
    c.clip(i, ov["start"], ov["duration"], FULL,
           f'<div id="{i}-t" class="ttl" style="top:{y - size * 0.6:.0f}px;font-size:{size}px">{text}</div>')
    c.tween(f'tl.fromTo("#{i}-t",{{y:{int(0.03 * H)},opacity:0}},{{y:0,opacity:1,duration:.32,ease:"power3.out"}},{ov["start"]:.3f});')
    c.fade_out(f"#{i}", ov["start"] + ov["duration"])


def build_numbered(c, ov):
    H = c.H
    i = c.uid("num")
    y = ov.get("y", 0.52) * H
    big, med = int(0.095 * H), int(0.062 * H)
    c.clip(i, ov["start"], ov["duration"], FULL,
           f'<div id="{i}-n" class="num" style="top:{y - big * 0.62:.0f}px;font-size:{med}px;transform-origin:50% 50%">'
           f'<b style="font-size:{big}px">{esc(ov["number"])}</b><span>{esc(ov["text"])}</span></div>')
    s = ov["start"]
    c.tween(f'tl.fromTo("#{i}-n",{{scale:.7,opacity:0}},{{scale:1.08,opacity:1,duration:.18,ease:"power2.out"}},{s:.3f});'
            f'tl.to("#{i}-n",{{scale:1,duration:.12,ease:"power2.inOut"}},{s + 0.18:.3f});')
    c.fade_out(f"#{i}", s + ov["duration"], 0.2)


def build_lower_third(c, ov):
    W, H = c.W, c.H
    v = W < H
    st, ss = int(0.036 * H if v else 0.052 * H), int(0.026 * H if v else 0.036 * H)
    pad = int(0.014 * H)
    i = c.uid("lt")
    inner = f'<div class="t" style="font-size:{st}px">{esc(ov["title"])}</div>'
    if ov.get("subtitle"):
        inner += f'<div class="s" style="font-size:{ss}px">{esc(ov["subtitle"])}</div>'
    y = int(ov.get("y", 0.58 if v else 0.70) * H)
    c.clip(i, ov["start"], ov["duration"], FULL,
           f'<div id="{i}-l" class="lt" style="left:{int(0.06 * W)}px;top:{y}px;padding:{pad}px {pad * 1.6:.0f}px">{inner}</div>')
    c.tween(f'tl.fromTo("#{i}-l",{{x:{-int(0.12 * W)},opacity:0}},{{x:0,opacity:1,duration:.35,ease:"power3.out"}},{ov["start"]:.3f});')
    c.fade_out(f"#{i}", ov["start"] + ov["duration"], 0.3)


# --------------------------------------------------------------------------- gráficos
def counter(c, sel, to, start, dur, dec=0, pre="", suf="", ease="power3.out"):
    c.tween(f'cnt("{sel}",{to},{start:.3f},{dur:.3f},{json.dumps({"dec": dec, "pre": pre, "suf": suf})},"{ease}");')


def build_stat(c, ov):
    W, H = c.W, c.H
    cw, ch = visual_size("stat", W, H)
    x, y = box_pos(ov.get("position", "top"), cw, ch, W, H)
    i = c.uid("stat")
    inner = (f'<div id="{i}-v" class="abs" style="left:0;width:100%;top:{ch * 0.10:.0f}px;text-align:center;'
             f'font-size:{ch * 0.46:.0f}px;font-weight:800;color:{c.theme["accent"]}">0</div>'
             f'<div class="abs" style="left:0;width:100%;bottom:{ch * 0.12:.0f}px;text-align:center;font-size:{ch * 0.14:.0f}px">{esc(ov.get("label", ""))}</div>')
    c.clip(i, ov["start"], ov["duration"], f"left:{x:.0f}px;top:{y:.0f}px;width:{cw:.0f}px;height:{ch:.0f}px;border-radius:{ch * 0.12:.0f}px", inner, "card")
    c.tween(f'tl.fromTo("#{i}",{{scale:.9,opacity:0}},{{scale:1,opacity:1,duration:.3,ease:"back.out(1.6)"}},{ov["start"]:.3f});')
    counter(c, f"#{i}-v", float(ov["value"]), ov["start"] + 0.1, 1.3, int(ov.get("decimals", 0)), ov.get("prefix", ""), ov.get("suffix", ""))
    c.fade_out(f"#{i}", ov["start"] + ov["duration"], 0.3)


def build_bar_line(c, ov):
    W, H, th = c.W, c.H, c.theme
    kind = ov.get("kind", "bar")
    cw, ch = visual_size("chart", W, H)
    x, y = box_pos(ov.get("position", "top"), cw, ch, W, H)
    i = c.uid("ch")
    labels, values = ov["labels"], [float(v) for v in ov["values"]]
    n, mx, mn = len(values), max(values), min(values)
    dec, pre, suf = int(ov.get("decimals", 0)), ov.get("prefix", ""), ov.get("suffix", "")
    fs, ft = ch * 0.075, ch * 0.095
    px0, pw, pb, ph = cw * 0.07, cw * 0.88, ch * 0.17, ch * 0.54            # área do gráfico (esq., largura, base, altura)
    inner = f'<div class="ct" style="left:{cw * 0.05:.0f}px;top:{ch * 0.05:.0f}px;font-size:{ft:.0f}px">{esc(ov.get("title", ""))}</div>'
    s, d = ov["start"], ov["duration"]
    if kind == "bar":
        hi = ov.get("highlight", "max")
        hi_idx = values.index(mx) if hi == "max" else (n - 1 if hi == "last" else hi if isinstance(hi, int) else None)
        slot = pw / n
        for k, v in enumerate(values):
            bw = slot * 0.62
            bh = ph * (v / mx) * 0.82
            color = th["accent"] if (hi_idx is None or k == hi_idx) else th["muted"]
            left = px0 + slot * k + (slot - bw) / 2
            inner += (f'<div id="{i}-b{k}" class="bar" style="left:{left:.0f}px;bottom:{pb:.0f}px;width:{bw:.0f}px;height:{bh:.0f}px;background:{color}">'
                      f'<div id="{i}-v{k}" class="val" style="top:-{fs * 1.5:.0f}px;font-size:{fs:.0f}px">0</div></div>'
                      f'<div class="lab" style="left:{left - slot * 0.19:.0f}px;width:{slot:.0f}px;bottom:{pb - fs * 1.6:.0f}px;font-size:{fs:.0f}px">{esc(labels[k])}</div>')
        inner += f'<div class="abs" style="left:{px0:.0f}px;width:{pw:.0f}px;bottom:{pb:.0f}px;height:2px;background:{th["muted"]}"></div>'
        c.clip(i, s, d, f"left:{x:.0f}px;top:{y:.0f}px;width:{cw:.0f}px;height:{ch:.0f}px;border-radius:{ch * 0.07:.0f}px", inner, "card")
        c.tween(f'tl.fromTo("#{i}",{{opacity:0,y:20}},{{opacity:1,y:0,duration:.25,ease:"power2.out"}},{s:.3f});')
        for k, v in enumerate(values):
            t0 = s + 0.15 + 0.4 * k / max(n - 1, 1) * 0.9
            c.tween(f'tl.fromTo("#{i}-b{k}",{{height:0}},{{height:{ph * (v / mx) * 0.82:.0f},duration:.8,ease:"power3.out"}},{t0:.3f});')
            counter(c, f"#{i}-v{k}", v, t0, 0.8, dec, pre, suf)
    else:  # linha
        rng = (mx - mn) or 1
        pts = []
        for k, v in enumerate(values):
            px_ = px0 + pw * (0.04 + 0.92 * k / max(n - 1, 1))
            py_ = ch - pb - ph * (0.10 + 0.78 * (v - mn) / rng)
            pts.append((px_, py_))
        d_path = "M" + " L".join(f"{a:.1f},{b:.1f}" for a, b in pts)
        area = d_path + f" L{pts[-1][0]:.1f},{ch - pb:.1f} L{pts[0][0]:.1f},{ch - pb:.1f} Z"
        inner += (f'<svg class="abs" style="left:0;top:0" width="{cw:.0f}" height="{ch:.0f}" viewBox="0 0 {cw:.0f} {ch:.0f}">'
                  f'<path id="{i}-area" d="{area}" fill="{th["accent"]}" opacity="0"/>'
                  f'<path id="{i}-ln" d="{d_path}" fill="none" stroke="{th["accent"]}" stroke-width="{ch * 0.018:.1f}" '
                  f'stroke-linecap="round" stroke-linejoin="round" pathLength="1" stroke-dasharray="1" stroke-dashoffset="1"/>'
                  + "".join(f'<circle id="{i}-p{k}" cx="{a:.1f}" cy="{b:.1f}" r="{ch * 0.025:.1f}" fill="{th["accent"]}" opacity="0"/>' for k, (a, b) in enumerate(pts))
                  + "</svg>")
        for k, (a, _) in enumerate(pts):
            inner += f'<div class="lab" style="left:{a - 40:.0f}px;width:80px;bottom:{pb - fs * 1.6:.0f}px;font-size:{fs:.0f}px">{esc(labels[k])}</div>'
        inner += f'<div id="{i}-v" class="val" style="left:{pts[-1][0]:.0f}px;top:{pts[-1][1] - fs * 1.9:.0f}px;font-size:{fs * 1.1:.0f}px;opacity:0">0</div>'
        c.clip(i, s, d, f"left:{x:.0f}px;top:{y:.0f}px;width:{cw:.0f}px;height:{ch:.0f}px;border-radius:{ch * 0.07:.0f}px", inner, "card")
        c.tween(f'tl.fromTo("#{i}",{{opacity:0,y:20}},{{opacity:1,y:0,duration:.25,ease:"power2.out"}},{s:.3f});')
        c.tween(f'tl.to("#{i}-ln",{{strokeDashoffset:0,duration:1.2,ease:"power2.inOut"}},{s + 0.2:.3f});'
                f'tl.to("#{i}-area",{{opacity:.14,duration:.6}},{s + 0.9:.3f});')
        for k in range(n):
            c.tween(f'tl.to("#{i}-p{k}",{{opacity:1,duration:.15}},{s + 0.2 + 1.2 * k / max(n - 1, 1):.3f});')
        c.tween(f'tl.to("#{i}-v",{{opacity:1,duration:.2}},{s + 1.2:.3f});')
        counter(c, f"#{i}-v", values[-1], s + 0.2, 1.2, dec, pre, suf)
    c.fade_out(f"#{i}", s + d, 0.3)


def build_steps(c, ov):
    W, H, th = c.W, c.H, c.theme
    cw, ch = visual_size("steps", W, H)
    x, y = box_pos(ov.get("position", "top"), cw, ch, W, H)
    i = c.uid("st")
    n, active = int(ov.get("count", 3)), int(ov.get("active", 1))
    dia = ch * 0.8
    inner = ""
    for k in range(n):
        cx = cw * (k + 0.5) / n
        on = (k + 1) == active
        col = th["accent"] if on else th["muted"]
        inner += (f'<div id="{i}-c{k}" class="ring" style="left:{cx - dia / 2:.0f}px;top:{(ch - dia) / 2:.0f}px;width:{dia:.0f}px;height:{dia:.0f}px;'
                  f'background:rgba(11,11,16,.62);border:{ch * 0.045:.0f}px {"dashed" if on else "solid"} {col};opacity:{1 if on else .55};'
                  f'display:flex;align-items:center;justify-content:center;color:{th["text"] if on else th["muted"]};'
                  f'font-size:{dia * 0.52:.0f}px;font-weight:800;font-style:italic">{k + 1}</div>')
    c.clip(i, ov["start"], ov["duration"], f"left:{x:.0f}px;top:{y:.0f}px;width:{cw:.0f}px;height:{ch:.0f}px;z-index:9", inner)
    for k in range(n):
        t0 = ov["start"] + (0 if (k + 1) == active else 0.05 * k)
        c.tween(f'tl.fromTo("#{i}-c{k}",{{scale:.6,opacity:0}},{{scale:1,opacity:{1 if (k + 1) == active else .55},duration:.35,ease:"back.out(2.2)"}},{t0:.3f});')
    c.fade_out(f"#{i}", ov["start"] + ov["duration"], 0.25)


def build_cards(c, ov, assets_dir):
    W, H, th = c.W, c.H, c.theme
    cw, ch = visual_size("cards", W, H)
    x, y = box_pos(ov.get("position", "top"), cw, ch, W, H)
    i = c.uid("cd")
    items = ov["items"]
    n = len(items)
    side = min(ch * 0.86, cw / (n * 1.25))
    gap = side * 0.22
    x0 = (cw - (n * side + (n - 1) * gap)) / 2
    inner = ""
    for k, it in enumerate(items):
        if it.get("image"):
            dst = assets_dir / Path(it["image"]).name
            shutil.copy2(it["image"], dst)
            body = f'<img src="assets/{esc(dst.name)}" style="width:72%;height:72%;object-fit:contain">'
        else:
            body = esc(it.get("text", ""))
        inner += (f'<div id="{i}-s{k}" class="sq" style="left:{x0 + k * (side + gap):.0f}px;top:{(ch - side) / 2:.0f}px;'
                  f'width:{side:.0f}px;height:{side:.0f}px;font-size:{side * 0.2:.0f}px;border-width:{side * 0.035:.0f}px">{body}</div>')
    c.clip(i, ov["start"], ov["duration"], f"left:{x:.0f}px;top:{y:.0f}px;width:{cw:.0f}px;height:{ch:.0f}px;z-index:9", inner)
    for k in range(n):
        c.tween(f'tl.fromTo("#{i}-s{k}",{{scale:.5,opacity:0}},{{scale:1,opacity:1,duration:.35,ease:"back.out(2.2)"}},{ov["start"] + 0.18 * k:.3f});')
    c.fade_out(f"#{i}", ov["start"] + ov["duration"], 0.25)


def build_pillars(c, ov, assets_dir):
    W, H, th = c.W, c.H, c.theme
    i = c.uid("pl")
    labels, values = ov["labels"], [float(v) for v in ov["values"]]
    colors = ov.get("colors") or [th["accent"]] * len(values)
    n, mx = len(values), max(values)
    dec, pre, suf = int(ov.get("decimals", 0)), ov.get("prefix", ""), ov.get("suffix", "")
    s, d = ov["start"], ov["duration"]
    bw = W / (n * 1.7)
    dx, dy = bw * 0.32, bw * 0.2
    base = H * 0.16                                                         # distância da base ao rodapé
    fs = H * 0.016
    inner = (f'<div class="abs" style="left:0;width:100%;top:{H * 0.20:.0f}px;text-align:center;font-size:{H * 0.034:.0f}px;font-weight:800;color:{th["accent"]}">{esc(ov.get("title", ""))}</div>'
             f'<div class="abs" style="left:0;width:100%;top:{H * 0.20 + H * 0.045:.0f}px;text-align:center;font-size:{H * 0.031:.0f}px;font-weight:800">{esc(ov.get("subtitle", ""))}</div>')
    svg, extras = "", ""
    for k, v in enumerate(values):
        x = W * (k + 0.5) / n - bw / 2
        h = (0.20 + 0.30 * v / mx) * H
        col = colors[k]
        yb, yt = H - base, H - base - h
        rgb = tuple(int(col.lstrip("#")[j:j + 2], 16) for j in (0, 2, 4))
        light = "#%02x%02x%02x" % tuple(min(255, int(ch_ * 1.25 + 20)) for ch_ in rgb)
        dark = "#%02x%02x%02x" % tuple(int(ch_ * 0.65) for ch_ in rgb)
        svg += (f'<g id="{i}-g{k}"><polygon points="{x:.1f},{yb:.1f} {x + bw:.1f},{yb:.1f} {x + bw:.1f},{yt:.1f} {x:.1f},{yt:.1f}" fill="{col}"/>'
                f'<polygon points="{x:.1f},{yt:.1f} {x + bw:.1f},{yt:.1f} {x + bw + dx:.1f},{yt - dy:.1f} {x + dx:.1f},{yt - dy:.1f}" fill="{light}"/>'
                f'<polygon points="{x + bw:.1f},{yb:.1f} {x + bw + dx:.1f},{yb - dy:.1f} {x + bw + dx:.1f},{yt - dy:.1f} {x + bw:.1f},{yt:.1f}" fill="{dark}"/></g>')
        extras += (f'<div id="{i}-v{k}" class="val" style="left:{x + bw / 2:.0f}px;top:{yt - dy - fs * 2.2:.0f}px;font-size:{fs * 1.2:.0f}px">0</div>'
                   f'<div class="lab" style="left:{x + bw / 2 - bw:.0f}px;width:{2 * bw:.0f}px;top:{yb + fs * 0.9:.0f}px;font-size:{fs * 1.1:.0f}px;font-weight:700">{esc(labels[k])}</div>')
        if ov.get("logos") and ov["logos"][k]:
            dst = assets_dir / Path(ov["logos"][k]).name
            shutil.copy2(ov["logos"][k], dst)
            ls = bw * 0.55
            extras += (f'<img id="{i}-lg{k}" class="abs" src="assets/{esc(dst.name)}" style="left:{x + bw / 2 - ls / 2:.0f}px;'
                       f'top:{yb - h * 0.82 - ls / 2:.0f}px;width:{ls:.0f}px;height:{ls:.0f}px;object-fit:contain">')
    inner += f'<svg class="abs" style="left:0;top:0" width="{W}" height="{H}" viewBox="0 0 {W} {H}">{svg}</svg>{extras}'
    c.clip(i, s, d, "left:0;top:0;width:100%;height:100%", inner, "full")
    c.tween(f'tl.fromTo("#{i}",{{opacity:0}},{{opacity:1,duration:.3}},{s:.3f});')
    for k, v in enumerate(values):
        t0 = s + 0.2 + 0.35 * k / max(n - 1, 1)
        h = (0.20 + 0.30 * v / mx) * H
        c.tween(f'tl.fromTo("#{i}-g{k}",{{scaleY:0,svgOrigin:"{W * (k + 0.5) / n:.1f} {H - base:.1f}"}},{{scaleY:1,duration:.9,ease:"power3.out"}},{t0:.3f});'
                f'tl.fromTo("#{i}-v{k}",{{y:{h:.0f}}},{{y:0,duration:.9,ease:"power3.out"}},{t0:.3f});')
        if ov.get("logos") and ov["logos"][k]:
            c.tween(f'tl.fromTo("#{i}-lg{k}",{{y:{h * 0.82:.0f},opacity:0}},{{y:0,opacity:1,duration:.9,ease:"power3.out"}},{t0:.3f});')
        counter(c, f"#{i}-v{k}", v, t0, 0.9, dec, pre, suf)
    c.fade_out(f"#{i}", s + d, 0.3)


# --------------------------------------------------------------------------- b-roll (fotos e vídeos inseridos)
def build_broll(c, ov, assets_dir):
    """Foto ou vídeo por cima do vídeo principal, abaixo das legendas (z-index 5).
    layout "full": tela cheia. layout "janela": cartão arredondado no topo, rosto continua visível embaixo.
    Fotos ganham zoom lento (Ken Burns). Vídeos devem vir já preparados (prep_broll_video): sem áudio, no tamanho certo."""
    W, H = c.W, c.H
    i = c.uid("br")
    s, d = ov["start"], ov["duration"]
    src = Path(ov["file"])
    dst = assets_dir / src.name
    if src.resolve() != dst.resolve():
        shutil.copy2(src, dst)
    if ov.get("layout") == "janela":
        bw, bh = W * 0.88, H * 0.40
        box = (f"left:{(W - bw) / 2:.0f}px;top:{H * 0.08:.0f}px;width:{bw:.0f}px;height:{bh:.0f}px;border-radius:{W * 0.035:.0f}px;"
               f"overflow:hidden;box-shadow:0 {H * 0.01:.0f}px {H * 0.03:.0f}px rgba(0,0,0,.5);border:{max(4, W * 0.005):.0f}px solid {c.theme['accent']}")
    else:
        box = "left:0;top:0;width:100%;height:100%;overflow:hidden"
    if ov.get("kind") == "video":
        c.html.append(f'<video id="{i}" class="clip" src="assets/{esc(dst.name)}" muted playsinline data-start="{s:.3f}" '
                      f'data-duration="{d:.3f}" data-track-index="{1 + c.n}" data-has-audio="false" '
                      f'style="position:absolute;{box};object-fit:cover;z-index:5"></video>')
        c.tween(f'tl.fromTo("#{i}",{{opacity:0}},{{opacity:1,duration:.2}},{s:.3f});')
    else:
        z0, z1 = (1.0, 1.12) if ov.get("zoom", "in") == "in" else (1.12, 1.0)
        inner = f'<img id="{i}-im" src="assets/{esc(dst.name)}" style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover">'
        c.clip(i, s, d, f"{box};z-index:5", inner)
        c.tween(f'tl.fromTo("#{i}",{{opacity:0}},{{opacity:1,duration:.2}},{s:.3f});')
        c.tween(f'tl.fromTo("#{i}-im",{{scale:{z0}}},{{scale:{z1},duration:{d:.3f},ease:"none"}},{s:.3f});')
    c.fade_out(f"#{i}", s + d, 0.2)


def build_endcard(c, ov):
    """Cartão de encerramento: fundo na cor da marca, chamada grande e assinatura."""
    W, H, th = c.W, c.H, c.theme
    i = c.uid("end")
    s, d = ov["start"], ov["duration"]
    bg = ov.get("background", th.get("brand", "#224289"))
    big, small = int(0.052 * H if W < H else 0.075 * H), int(0.026 * H if W < H else 0.04 * H)
    text = re.sub(r"\*(.+?)\*", rf'<span style="color:{th["accent"]}">\1</span>', esc(ov.get("text", "")))
    inner = (f'<div class="abs" style="inset:0;background:{bg};opacity:.94"></div>'
             f'<div id="{i}-t" class="abs" style="left:8%;width:84%;top:{H * 0.40:.0f}px;text-align:center;color:{th["text"]};'
             f'font-weight:800;text-transform:uppercase;font-size:{big}px;line-height:1.1">{text}</div>'
             f'<div id="{i}-b" class="abs" style="left:{W * 0.42:.0f}px;width:{W * 0.16:.0f}px;top:{H * 0.40 + big * 2.7:.0f}px;'
             f'height:{max(6, H * 0.005):.0f}px;background:{th["accent"]}"></div>'
             f'<div id="{i}-s" class="abs" style="left:0;width:100%;top:{H * 0.40 + big * 2.7 + small * 1.2:.0f}px;text-align:center;'
             f'color:{th["text"]};font-weight:600;font-size:{small}px;letter-spacing:.08em">{esc(ov.get("subtext", ""))}</div>')
    c.clip(i, s, d, "left:0;top:0;width:100%;height:100%;z-index:14", inner)
    c.tween(f'tl.fromTo("#{i}",{{opacity:0}},{{opacity:1,duration:.3}},{s:.3f});'
            f'tl.fromTo("#{i}-t",{{y:{int(0.03 * H)},opacity:0}},{{y:0,opacity:1,duration:.4,ease:"power3.out"}},{s + 0.15:.3f});'
            f'tl.fromTo("#{i}-b",{{scaleX:0}},{{scaleX:1,duration:.35,ease:"power2.out"}},{s + 0.35:.3f});'
            f'tl.fromTo("#{i}-s",{{opacity:0}},{{opacity:1,duration:.3}},{s + 0.5:.3f});')


# --------------------------------------------------------------------------- projeto
def ensure_gsap(project):
    """Coloca gsap.min.js dentro do projeto: o Chrome do render não precisa de internet e a saída é reprodutível."""
    dst = project / "gsap.min.js"
    if dst.exists():
        return "gsap.min.js"
    if shutil.which("npm"):
        (project / "package.json").write_text('{"name":"edicao","private":true,"type":"module"}', encoding="utf-8")
        subprocess.run(["npm", "install", f"gsap@{GSAP_VERSION}", "--silent", "--no-audit", "--no-fund"],
                       cwd=project, capture_output=True)
        src = project / "node_modules" / "gsap" / "dist" / "gsap.min.js"
        if src.exists():
            shutil.copy2(src, dst)
            return "gsap.min.js"
    print("AVISO: não consegui instalar o GSAP localmente; usando CDN (precisa de internet no render).", file=sys.stderr)
    return f"https://cdn.jsdelivr.net/npm/gsap@{GSAP_VERSION}/dist/gsap.min.js"


def build_project(project, video, words, spec, joins=None):
    """Escreve project/index.html (+ vídeo, fontes, gsap). Retorna o caminho do index.html."""
    project = Path(project)
    (project / "assets").mkdir(parents=True, exist_ok=True)
    info = probe(video)
    W, H, dur = info["width"], info["height"], round(info["duration"], 3)
    theme = {**DEFAULT_THEME, "muted": "#6B7280", **spec.get("theme", {})}
    sub = spec.get("subtitles", {})
    overlays = spec.get("overlays", [])

    shutil.copy2(video, project / "base.mp4")
    font_name = spec.get("font")
    family = pick_font(font_name)
    face = ""
    hit = local_font(font_name) or local_font(family)
    if hit:
        (project / "fonts").mkdir(exist_ok=True)
        shutil.copy2(hit[1], project / "fonts" / Path(hit[1]).name)
        face = (f'@font-face{{font-family:"{hit[0]}";src:url("fonts/{Path(hit[1]).name}");font-weight:100 900;font-style:normal}}')
    stack = f'"{family}","Montserrat","Poppins","Inter","Arial",sans-serif'

    style = sub.get("style", "ref")
    pre = SUB_PRESETS.get(style, SUB_PRESETS["ref"])
    base_px = int(sub.get("size") or (0.052 * H if W < H else 0.062 * H))
    bold = sub.get("bold", pre.get("bold", True))
    italic = sub.get("italic", pre.get("italic", False))
    css = (CSS.replace("@W@", str(W)).replace("@H@", str(H)).replace("@FONT_STACK@", stack)
           .replace("@TEXT@", theme["text"]).replace("@ACCENT@", theme["accent"])
           .replace("@CAP_SIZE@", str(base_px)).replace("@CAP_WEIGHT@", "700" if bold else "500").replace("@CAP_STYLE@", "italic" if italic else "normal")
           .replace("@SHADOW_Y@", str(max(3, int(base_px * pre.get("shadow", 0.05))))).replace("@SHADOW_B@", str(max(6, int(base_px * 0.14))))
           .replace("@STROKE@", str(max(3, int(base_px * 0.09)))).replace("@BAR@", str(max(6, int(0.006 * H))))
           .replace("@DASH@", str(max(4, int(0.004 * H)))))

    c = Comp(W, H, theme)
    if sub.get("enabled", True) and words:
        quiet = [(o["start"], o["start"] + o["duration"]) for o in overlays if o.get("type") in ("numbered_title", "end_card")]
        ws = [w for w in words if not any(a - 0.05 <= w["start"] < b for a, b in quiet)]
        build_captions(c, ws, sub, theme, base_px)
    for ov in overlays:
        t = ov.get("type")
        if t == "title":
            build_title(c, ov, base_px)
        elif t == "numbered_title":
            build_numbered(c, ov)
        elif t == "lower_third":
            build_lower_third(c, ov)
        elif t == "stat":
            build_stat(c, ov)
        elif t == "chart":
            build_bar_line(c, ov)
        elif t == "steps":
            build_steps(c, ov)
        elif t == "cards":
            build_cards(c, ov, project / "assets")
        elif t == "pillars":
            build_pillars(c, ov, project / "assets")
        elif t == "end_card":
            build_endcard(c, ov)
        elif t == "broll":
            build_broll(c, ov, project / "assets")

    punch = spec.get("punch_in", {})
    zoom_js = ""
    if punch.get("enabled"):
        for a, b, z in punch_schedule(dur, joins or [], punch):
            zoom_js += f'tl.set("#a-roll",{{scale:{z:.3f},transformOrigin:"50% 30%"}},{a:.3f});'

    gsap_src = ensure_gsap(project)
    doc = f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width={W}, height={H}"/>
<script src="{gsap_src}"></script>
<style>{face}{css}</style>
</head>
<body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{dur}" data-width="{W}" data-height="{H}">
<video id="a-roll" class="clip" src="base.mp4" playsinline data-start="0" data-duration="{dur}" data-track-index="0" data-has-audio="true"></video>
{chr(10).join(c.html)}
</div>
<script>
const fmtBR=(v,o)=>{{const s=v.toLocaleString("pt-BR",{{minimumFractionDigits:o.dec,maximumFractionDigits:o.dec}});return (o.pre||"")+s+(o.suf||"")}};
const tl=gsap.timeline({{paused:true}});
function cnt(sel,to,t0,d,o,ease){{const el=document.querySelector(sel);const st={{v:0}};
  tl.to(st,{{v:to,duration:d,ease:ease,onUpdate(){{el.textContent=fmtBR(st.v,o)}}}},t0);}}
{zoom_js}
{chr(10).join(c.js)}
window.__timelines["main"]=tl;
</script>
</body>
</html>
"""
    (project / "index.html").write_text(doc, encoding="utf-8")
    (project / "hyperframes.json").write_text(json.dumps({
        "$schema": "https://hyperframes.heygen.com/schema/hyperframes.json",
        "registry": "https://raw.githubusercontent.com/heygen-com/hyperframes/main/registry",
        "paths": {"blocks": "compositions", "components": "compositions/components", "assets": "assets"},
        "media": {"autoProxy": True}}, indent=2), encoding="utf-8")
    (project / "meta.json").write_text(json.dumps({"id": project.name, "name": project.name}), encoding="utf-8")
    return project / "index.html"


def render(project, output, draft=False, fps=30):
    """Chama `npx hyperframes render`. Use HYPERFRAMES_BROWSER_PATH para apontar um Chrome já instalado."""
    if not shutil.which("npx"):
        sys.exit("npx não encontrado. Instale o Node.js 22+ (https://nodejs.org).")
    cmd = ["npx", "--yes", f"hyperframes@{HF_VERSION}", "render", "-q", "draft" if draft else "looks",
           "-f", str(fps), "-o", str(Path(output).resolve())]
    res = subprocess.run(cmd, cwd=project, text=True, capture_output=True)
    if res.returncode != 0:
        tail = (res.stdout + res.stderr)[-2500:]
        raise RuntimeError(f"hyperframes render falhou:\n{tail}")
    return Path(output)


def main():
    from edit_video import deep_merge, PRESET_DIR          # reutiliza a lógica de presets
    from common import load_json
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video")
    ap.add_argument("--transcript")
    ap.add_argument("--spec")
    ap.add_argument("--preset")
    ap.add_argument("--project", default="hf_project")
    ap.add_argument("-o", "--output", required=True)
    ap.add_argument("--draft", action="store_true")
    a = ap.parse_args()
    spec = load_json(a.spec) if a.spec else {}
    if a.preset or spec.get("preset"):
        spec = deep_merge(load_json(PRESET_DIR / f"{a.preset or spec['preset']}.json"), spec)
    words = load_json(a.transcript)["words"] if a.transcript else None
    build_project(Path(a.project), a.video, words, spec)
    print("Renderizando com HyperFrames...")
    print("Pronto:", render(Path(a.project), a.output, a.draft))


if __name__ == "__main__":
    main()
