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
from common import local_font, pick_font, probe, punch_schedule, text_width

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
.cap-in{font-size:@CAP_SIZE@px;text-align:center;white-space:nowrap;color:@TEXT@;line-height:@CAP_LH@;font-weight:@CAP_WEIGHT@;font-style:@CAP_STYLE@;
  text-shadow:0 @SHADOW_Y@px @SHADOW_B@px rgba(0,0,0,.62)}
.cap-in .l2{color:@ACCENT@;font-size:@L2@em;text-transform:uppercase}
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
.glass{position:absolute;z-index:9;background:linear-gradient(180deg,rgba(40,40,46,.62),rgba(12,12,16,.72));
  border:2px solid rgba(255,255,255,.14);box-shadow:0 18px 40px rgba(0,0,0,.35);overflow:hidden;
  display:flex;align-items:center;justify-content:center;backdrop-filter:blur(14px)}
.glow{color:@ACCENT@;font-weight:800;line-height:1;white-space:nowrap;
  text-shadow:0 0 18px rgba(249,212,26,.55),0 0 42px rgba(249,212,26,.35),0 6px 10px rgba(0,0,0,.45)}
.cta{position:absolute;z-index:14;background:#fff;display:flex;align-items:center;overflow:hidden;
  box-shadow:0 12px 34px rgba(0,0,0,.28);font-family:"Montserrat","Poppins","Inter",Arial,sans-serif}
.cta .av{border-radius:50%;background:conic-gradient(#F58529,#DD2A7B,#8134AF,#515BD4,#F58529);flex:none;
  display:flex;align-items:center;justify-content:center}
.cta .av>*{border-radius:50%;border:4px solid #fff;object-fit:cover;background:#E5E7EB;display:flex;align-items:center;
  justify-content:center;color:#111;font-weight:800}
.cta .hd{color:#262626;font-weight:800;white-space:nowrap;flex:1;overflow:hidden;text-overflow:ellipsis}
.cta .bt{position:relative;flex:none;border-radius:.32em;display:flex;align-items:center;justify-content:center;white-space:nowrap}
.cta .b1{border:2px solid #D4D4D8;color:#A1A1AA;background:#fff}
.cta .b2{position:absolute;inset:0;color:#fff;background:linear-gradient(90deg,#4C1D95,#9D174D 60%,#C2410C);opacity:0}
.cursor{position:absolute;z-index:15;width:0;height:0}
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

    def __init__(self, W, H, theme, faces=None, family="Arial"):
        self.W, self.H, self.theme, self.family = W, H, theme, family
        self.html, self.js, self.n = [], [], 0
        self.faces = faces or []          # [(t, x0, y0, x1, y1)] em px, já com o zoom aplicado
        self.obst = []                    # overlays já posicionados: (t0, t1, x0, y0, x1, y1)
        v = W < H
        self.ymin, self.ymax = (0.03 * H, 0.80 * H) if v else (0.04 * H, 0.94 * H)   # 20% de baixo = interface do Reels
        self.m = 0.015 * H                # folga entre texto e rosto
        self.cap_band = 0                 # altura reservada para a legenda logo abaixo do rosto (definida no build)

    # ---------------- layout sem cobrir o rosto
    def _obstacles(self, t0, t1, overlays=True, band=False):
        fs = [b[1:] for b in self.faces if t0 - 0.15 <= b[0] <= t1 + 0.15]
        obs = list(fs)
        if band and self.cap_band:        # overlays não ocupam a faixa da legenda embaixo do rosto
            obs += [(0, f[3], self.W, f[3] + self.m + self.cap_band) for f in fs]
        if overlays:
            obs += [o[2:] for o in self.obst if o[0] < t1 and o[1] > t0]
        return obs

    def _hits(self, y, h, x0, x1, obs):
        m = self.m
        return [o for o in obs if x0 < o[2] and x1 > o[0] and y < o[3] + m and y + h > o[1] - m]

    def place(self, y, h, t0, t1, x0=0, x1=None, prefer="down", overlays=True, band=False, strict=False):
        """Topo (px) mais próximo de y em que a caixa não encosta no rosto nem em outro overlay; None se não couber.
        strict=True só aceita posições no sentido de 'prefer' (acima de y para "up", abaixo para "down")."""
        x1 = self.W if x1 is None else x1
        obs = self._obstacles(t0, t1, overlays, band)
        lo, hi = self.ymin, self.ymax - h
        if hi < lo:
            return None
        y = min(max(y, lo), hi)
        if not self._hits(y, h, x0, x1, obs):
            return y
        cands = []
        for o in obs:
            cands += [o[3] + self.m + 1, o[1] - self.m - h - 1]
        cands = [cy for cy in cands if lo <= cy <= hi and not self._hits(cy, h, x0, x1, obs)
                 and not (strict and (cy > y if prefer == "up" else cy < y))]
        if not cands:
            return None
        pen = (lambda cy: abs(cy - y) + (0 if cy >= y else 0.25 * self.H)) if prefer == "down" else \
              (lambda cy: abs(cy - y) + (0 if cy <= y else 0.25 * self.H))
        return min(cands, key=pen)

    def fit(self, y, h, t0, t1, x0, x1, prefer="down", scales=(1, 0.85, 0.72, 0.6, 0.5, 0.42), register=True, label=""):
        """Tenta posicionar; se não couber, diminui. Retorna (y, escala) e registra a caixa como obstáculo.
        1ª passada: só no sentido preferido (ex.: acima do rosto), diminuindo; 2ª: qualquer lugar livre."""
        cx = (x0 + x1) / 2
        for strict in (True, False):
            for k in scales:
                hw = (x1 - x0) * k / 2
                ny = self.place(y, h * k, t0, t1, cx - hw, cx + hw, prefer, band=True, strict=strict)
                if ny is not None:
                    if register:
                        self.obst.append((t0, t1, cx - hw, ny, cx + hw, ny + h * k))
                    return ny, k
        print(f"AVISO: {label or 'elemento'} em {t0:.1f}s não achou lugar livre do rosto; mantido na posição original.",
              file=sys.stderr)
        if register:
            self.obst.append((t0, t1, x0, y, x1, y + h))
        return y, 1.0

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
    lh, ks = float(opts.get("line_height", 1.12)), float(opts.get("keyword_scale", 1.15))

    def safe_center(lines, start, end):
        """Centro vertical (fração da altura) da legenda, fora do rosto e dos overlays."""
        if opts.get("_fixed") or (not c.faces and not c.obst):
            return pos_y
        hgt = sum(base_px * sc * lh for _, sc in lines)
        wid = max(text_width(t, base_px * sc, c.family) * (1.12 if sc > 1 else 1) for t, sc in lines) + 0.04 * W
        y = c.place(pos_y * H - hgt / 2, hgt, start, end, (W - wid) / 2, (W + wid) / 2, "down")
        if y is None:                     # sem lugar: prefere encostar num overlay a cobrir o rosto
            y = c.place(pos_y * H - hgt / 2, hgt, start, end, (W - wid) / 2, (W + wid) / 2, "down", overlays=False)
        if y is None:
            print(f"AVISO: legenda em {start:.1f}s sem lugar livre do rosto; mantida no centro.", file=sys.stderr)
            return pos_y
        return (y + hgt / 2) / H

    for gi, g in enumerate(groups):
        start = g[0]["start"]
        end = g[-1]["end"] + 0.2
        if gi + 1 < len(groups):
            end = min(end, groups[gi + 1][0]["start"])
        end = max(end, start + 0.15)
        i = c.uid("cap")
        cls = "cap-in" + (" cap-viral" if style == "viral" else " cap-box" if style == "box" else "")
        if preset.get("stack"):
            ws = [(w["word"].strip("*").rstrip(",.;:"), is_emphasis(w["word"], opts)) for w in g]   # sem vírgula/ponto, como no Reel
            k = len(ws)
            while k > 0 and ws[k - 1][1]:
                k -= 1
            plain, key = ws[:k], ws[k:]
            l1, l2 = " ".join(t for t, _ in plain), " ".join(t for t, _ in key)
            if key and plain:
                inner = f'<div class="l1">{esc(l1)}</div><div class="l2">{esc(l2)}</div>'
                lines = [(l1, 1), (l2.upper(), ks)]
            elif key:
                inner = f'<div class="l2">{esc(l2)}</div>'
                lines = [(l2.upper(), ks)]
            else:
                inner = '<div class="l1">' + " ".join(f'<span class="k">{esc(t)}</span>' if e else esc(t) for t, e in ws) + "</div>"
                lines = [(" ".join(t for t, _ in ws), 1)]
            py = safe_center(lines, start, end)
            c.clip(i, start, end - start, FULL, f'<div class="cap" style="top:{py * 100:.1f}%"><div id="{i}-in" class="{cls}">{inner}</div></div>')
        else:
            spans = "".join(f'<span id="{i}-w{j}">{esc(w["word"])}</span> ' for j, w in enumerate(g))
            py = safe_center([(" ".join(w["word"] for w in g), 1.15 if style == "viral" else 1)], start, end)
            c.clip(i, start, end - start, FULL, f'<div class="cap" style="top:{py * 100:.1f}%"><div id="{i}-in" class="{cls}">{spans.strip()}</div></div>')
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
    nl = max(1, round(text_width(re.sub(r"<.+?>", "", text), size, c.family) / (0.84 * c.W) + 0.49))
    ty, k = c.fit(y - size * 0.6, size * 1.2 * nl, ov["start"], ov["start"] + ov["duration"], 0.08 * c.W, 0.92 * c.W,
                  "down" if pos != "top" else "up", label="title")
    size = int(size * k)
    c.clip(i, ov["start"], ov["duration"], FULL,
           f'<div id="{i}-t" class="ttl" style="top:{ty:.0f}px;font-size:{size}px">{text}</div>')
    c.tween(f'tl.fromTo("#{i}-t",{{y:{int(0.03 * H)},opacity:0}},{{y:0,opacity:1,duration:.32,ease:"power3.out"}},{ov["start"]:.3f});')
    c.fade_out(f"#{i}", ov["start"] + ov["duration"])


def build_numbered(c, ov):
    H = c.H
    i = c.uid("num")
    y = ov.get("y", 0.52) * H
    big, med = int(0.095 * H), int(0.062 * H)
    wid = text_width(f'{ov["number"]} {ov["text"]}'.upper(), med, c.family) + big * 0.6
    ty, k = c.fit(y - big * 0.62, big * 1.2, ov["start"], ov["start"] + ov["duration"], (c.W - wid) / 2, (c.W + wid) / 2,
                  label="numbered_title")
    big, med = int(big * k), int(med * k)
    c.clip(i, ov["start"], ov["duration"], FULL,
           f'<div id="{i}-n" class="num" style="top:{ty:.0f}px;font-size:{med}px;transform-origin:50% 50%">'
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
    lw = max(text_width(ov["title"], st, c.family), text_width(ov.get("subtitle", ""), ss, c.family)) + pad * 3.2
    y, _ = c.fit(y, st * 1.3 + (ss * 1.3 if ov.get("subtitle") else 0) + 2 * pad, ov["start"], ov["start"] + ov["duration"],
                 0.06 * W, 0.06 * W + lw, scales=(1,), label="lower_third")
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
    y, _ = c.fit(y, ch, ov["start"], ov["start"] + ov["duration"], x, x + cw,
                 "up" if y < H * 0.4 else "down", scales=(1,), label="stat")
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
    y, _ = c.fit(y, ch, ov["start"], ov["start"] + ov["duration"], x, x + cw,
                 "up" if y < H * 0.4 else "down", scales=(1,), label="chart")
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
    y, _ = c.fit(y, ch, ov["start"], ov["start"] + ov["duration"], x, x + cw,
                 "up" if y < H * 0.4 else "down", scales=(1,), label="steps")
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
    y, _ = c.fit(y, ch, ov["start"], ov["start"] + ov["duration"], x, x + cw,
                 "up" if y < H * 0.4 else "down", scales=(1,), label="cards")
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


# --------------------------------------------------------------------------- elementos do Reel de referência
def build_glass_badge(c, ov):
    """Caixa de vidro escura no topo com texto amarelo brilhante que entra rolando de baixo (ex.: "$$$")."""
    W, H = c.W, c.H
    i = c.uid("gb")
    bw, bh = ov.get("width", 0.67) * W, ov.get("height", 0.15) * H
    x, y = (W - bw) / 2, ov.get("y", 0.10) * H
    fs = ov.get("size", 0.12) * H
    y, k = c.fit(y, bh, ov["start"], ov["start"] + ov["duration"], x, x + bw, "up", label="glass_badge")
    bw, bh, fs = bw * k, bh * k, fs * k
    x = (W - bw) / 2
    inner = f'<div id="{i}-t" class="glow" style="font-size:{fs:.0f}px">{esc(ov["text"])}</div>'
    c.clip(i, ov["start"], ov["duration"], f"left:{x:.0f}px;top:{y:.0f}px;width:{bw:.0f}px;height:{bh:.0f}px;border-radius:{bh * 0.12:.0f}px", inner, "glass")
    s = ov["start"]
    c.tween(f'tl.fromTo("#{i}",{{opacity:0,scale:.92}},{{opacity:1,scale:1,duration:.22,ease:"power2.out"}},{s:.3f});'
            f'tl.fromTo("#{i}-t",{{yPercent:120,filter:"blur(10px)"}},{{yPercent:0,filter:"blur(0px)",duration:.45,ease:"back.out(1.5)"}},{s + 0.05:.3f});')
    c.fade_out(f"#{i}", s + ov["duration"], 0.25)


def build_big_number(c, ov):
    """Número gigante amarelo com brilho no topo, contando até o valor (ex.: "$10,000")."""
    W, H = c.W, c.H
    i = c.uid("bn")
    y = ov.get("y", 0.09) * H
    fs = ov.get("size", 0.085) * H
    txt = ov.get("text")
    sample = txt or f'{ov.get("prefix", "")}{float(ov.get("value", 0)):,.{int(ov.get("decimals", 0))}f}{ov.get("suffix", "")}'
    wid = min(W, text_width(sample, fs, c.family) * 1.05)
    y, k = c.fit(y - fs * 0.08, fs * 1.16, ov["start"], ov["start"] + ov["duration"], (W - wid) / 2, (W + wid) / 2, "up",
                 label="big_number")
    y, fs = y + fs * 0.08 * k, fs * k
    inner = (f'<div id="{i}-v" class="glow abs" style="left:0;width:100%;top:{y:.0f}px;text-align:center;font-size:{fs:.0f}px">'
             f'{esc(txt) if txt else "0"}</div>')
    c.clip(i, ov["start"], ov["duration"], FULL, inner)
    s = ov["start"]
    c.tween(f'tl.fromTo("#{i}-v",{{scale:.6,opacity:0}},{{scale:1,opacity:1,duration:.3,ease:"back.out(2)"}},{s:.3f});')
    if not txt:
        counter(c, f"#{i}-v", float(ov["value"]), s, ov.get("count_duration", 0.9), int(ov.get("decimals", 0)),
                ov.get("prefix", ""), ov.get("suffix", ""))
    c.fade_out(f"#{i}", s + ov["duration"], 0.25)


CURSOR_SVG = ('<svg width="{s}" height="{s}" viewBox="0 0 24 24"><path d="M3 2 L3 19 L7.5 15 L10.5 22 L13.5 20.8 L10.6 14 L17 14 Z" '
              'fill="#fff" stroke="#111" stroke-width="1.4" stroke-linejoin="round"/></svg>')


def build_follow_cta(c, ov, assets_dir):
    """Cartão branco de perfil (foto, @, botão Seguir) que se abre, recebe um clique e vira "Seguindo"."""
    W, H = c.W, c.H
    i = c.uid("cta")
    cw, ch = ov.get("width", 0.66) * W, ov.get("height", 0.062) * H
    x, y = (W - cw) / 2, ov.get("y", 0.64) * H - ch / 2
    y, k = c.fit(y, ch, ov["start"], ov["start"] + ov["duration"], x, x + cw, label="follow_cta")
    cw, ch = cw * k, ch * k
    x = (W - cw) / 2
    pad = ch * 0.16
    av = ch - 2 * pad
    if ov.get("avatar"):
        dst = assets_dir / Path(ov["avatar"]).name
        shutil.copy2(ov["avatar"], dst)
        pic = f'<img src="assets/{esc(dst.name)}" style="width:{av - 8:.0f}px;height:{av - 8:.0f}px">'
    else:
        ini = esc((ov.get("handle", "?").lstrip("@")[:1] or "?").upper())
        pic = f'<div style="width:{av - 8:.0f}px;height:{av - 8:.0f}px;font-size:{av * 0.42:.0f}px">{ini}</div>'
    bw, bh = cw * 0.27, ch * 0.42
    fs = ch * 0.27
    handle = ov.get("handle", "@seuperfil").lstrip("@")
    room = cw - 2 * pad * 1.6 - av - pad * 0.9 - bw - pad
    hs = min(fs, room / (0.62 * max(len(handle), 1)))                      # diminui a fonte do @ se for longo
    follow, following = esc(ov.get("button", "Seguir")), esc(ov.get("button_done", "Seguindo"))
    inner = (f'<div class="av" style="width:{av:.0f}px;height:{av:.0f}px;margin-right:{pad * 0.9:.0f}px">{pic}</div>'
             f'<div class="hd" style="font-size:{hs:.0f}px;margin-right:{pad:.0f}px">{esc(handle)}</div>'
             f'<div class="bt b1" style="width:{bw:.0f}px;height:{bh:.0f}px;font-size:{fs * 0.82:.0f}px;font-weight:500">{follow}'
             f'<div id="{i}-b2" class="bt b2" style="font-size:{fs * 0.82:.0f}px;font-weight:600">{following}</div></div>')
    c.clip(i, ov["start"], ov["duration"],
           f"left:{x:.0f}px;top:{y:.0f}px;width:{cw:.0f}px;height:{ch:.0f}px;border-radius:{ch * 0.32:.0f}px;padding:0 {pad * 1.6:.0f}px", inner, "cta")
    cs = ch * 0.42
    bx, by = x + cw - pad * 1.6 - bw / 2, y + ch / 2
    c.clip(f"{i}-cur", ov["start"], ov["duration"], f"left:0;top:0;width:100%;height:100%;z-index:15",
           f'<div id="{i}-cu" class="abs" style="left:{bx:.0f}px;top:{by:.0f}px;width:{cs:.0f}px;height:{cs:.0f}px;opacity:0">{CURSOR_SVG.format(s=int(cs))}</div>')
    s = ov["start"]
    click = s + ov.get("click_at", 1.4)
    c.tween(f'tl.fromTo("#{i}",{{clipPath:"inset(40% 50% 40% 50% round {ch * 0.32:.0f}px)",opacity:0}},'
            f'{{clipPath:"inset(0% 0% 0% 0% round {ch * 0.32:.0f}px)",opacity:1,duration:.4,ease:"power3.out"}},{s:.3f});'
            f'tl.fromTo("#{i}-cu",{{x:{cs * 1.4:.0f},y:{cs * 1.6:.0f},opacity:0}},{{x:0,y:{cs * 0.1:.0f},opacity:1,duration:.5,ease:"power2.out"}},{click - 0.6:.3f});'
            f'tl.to("#{i}-cu",{{scale:.82,duration:.08,yoyo:true,repeat:1}},{click:.3f});'
            f'tl.to("#{i}-b2",{{opacity:1,duration:.12}},{click + 0.04:.3f});')
    c.fade_out(f"#{i}", s + ov["duration"], 0.3)
    c.fade_out(f"#{i}-cur", s + ov["duration"], 0.3)


def build_broll(c, ov, assets_dir):
    """Insere um clipe de apoio (b-roll) em tela cheia por cima do vídeo principal. O áudio da fala continua."""
    i = c.uid("br")
    dst = assets_dir / Path(ov["src"]).name
    shutil.copy2(ov["src"], dst)
    vol = float(ov.get("volume", 0))
    c.html.append(f'<video id="{i}" class="clip" src="assets/{esc(dst.name)}" playsinline muted data-start="{ov["start"]:.3f}" '
                  f'data-duration="{ov["duration"]:.3f}" data-media-start="{float(ov.get("from", 0)):.3f}" data-track-index="{2 + c.n}" '
                  f'data-has-audio="{"true" if vol > 0 else "false"}" data-volume="{vol}" '
                  f'style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover;z-index:5"></video>')


# --------------------------------------------------------------------------- projeto
def fixed_caption_slot(c, band, default_center):
    """Um só lugar para a legenda no vídeo todo, fora do rosto em todos os instantes.
    Prefere o centro padrão; se o rosto desce até lá, fica logo abaixo do ponto mais baixo do rosto;
    se não couber, diminui a legenda (até 70%) ou vai para cima da cabeça. Retorna (centro_px, escala)."""
    n = len(c.faces)
    bottom = sorted(f[4] for f in c.faces)[int(0.98 * (n - 1))]   # 98º percentil: ignora detecção errada isolada
    top = sorted(f[2] for f in c.faces)[int(0.02 * (n - 1))]
    for k in (1, 0.9, 0.8, 0.7):
        h = band * k
        if default_center - h / 2 >= bottom + c.m and default_center + h / 2 <= c.ymax:
            return default_center, k
        if bottom + c.m + h <= c.ymax:
            return bottom + c.m + h / 2, k
    for k in (1, 0.85, 0.7):
        if top - c.m - band * k >= c.ymin:
            return top - c.m - band * k / 2, k
    print("AVISO: o rosto ocupa quase todo o quadro; legenda fixa no limite inferior e reduzida.", file=sys.stderr)
    return c.ymax - band * 0.35, 0.7


def face_map(project, video, W, H, sched):
    """Caixas do rosto em px no quadro final (com o zoom do punch_in, origem 50% 30%). Cacheado em faces.json."""
    cache = Path(project) / "faces.json"
    try:
        if cache.exists() and cache.stat().st_mtime >= Path(video).stat().st_mtime:
            data = json.loads(cache.read_text(encoding="utf-8"))
        else:
            from face_track import track
            data = track(video)
            cache.write_text(json.dumps(data), encoding="utf-8")
    except Exception as e:                                     # sem OpenCV/modelo: segue sem proteção de rosto
        print(f"AVISO: detecção de rosto indisponível ({e}); textos podem cobrir o rosto.", file=sys.stderr)
        return []
    out = []
    for b in data["boxes"]:
        if b[1] is None:
            continue
        t = b[0]
        z = next((zz for a, bb, zz in sched if a <= t < bb), 1.0)
        ox, oy = 0.5 * W, 0.3 * H
        out.append((t, ox + (b[1] * W - ox) * z, oy + (b[2] * H - oy) * z, ox + (b[3] * W - ox) * z, oy + (b[4] * H - oy) * z))
    found = len(out)
    print(f"Rosto: {found}/{len(data['boxes'])} amostras com rosto; legendas e textos vão desviar dele.")
    return out


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
    hit = local_font(font_name)
    if hit:
        (project / "fonts").mkdir(exist_ok=True)
        shutil.copy2(hit[1], project / "fonts" / Path(hit[1]).name)
        face = (f'@font-face{{font-family:"{hit[0]}";src:url("fonts/{Path(hit[1]).name}");font-weight:100 900;font-style:normal}}')
    stack = f'"{family}","Montserrat","Poppins","Inter","Arial",sans-serif'

    style = sub.get("style", "ref")
    pre = SUB_PRESETS.get(style, SUB_PRESETS["ref"])
    base_px = int(sub.get("size") or (sub.get("size_ratio") or (0.052 if W < H else 0.062)) * H)
    bold = sub.get("bold", pre.get("bold", True))
    italic = sub.get("italic", pre.get("italic", False))

    punch = spec.get("punch_in", {})
    sched = punch_schedule(dur, joins or [], punch) if punch.get("enabled") else []
    faces = face_map(project, video, W, H, sched) if spec.get("face_safe", True) else []
    c = Comp(W, H, theme, faces, family)
    if sub.get("enabled", True) and words and faces:
        band = base_px * (1 + float(sub.get("keyword_scale", 1.15))) * float(sub.get("line_height", 1.12))
        if sub.get("placement", "fixed") == "fixed":
            center, k = fixed_caption_slot(c, band, sub.get("pos_y", pre.get("pos_y", 0.53)) * H)
            base_px = int(base_px * k)
            sub = {**sub, "pos_y": center / H, "_fixed": True}
            c.obst.append((0, dur + 1, 0, center - band * k / 2, W, center + band * k / 2))   # overlays não entram aqui
        else:
            c.cap_band = band
    css = (CSS.replace("@W@", str(W)).replace("@H@", str(H)).replace("@FONT_STACK@", stack)
           .replace("@TEXT@", theme["text"]).replace("@ACCENT@", theme["accent"])
           .replace("@CAP_SIZE@", str(base_px)).replace("@CAP_LH@", str(sub.get("line_height", 1.12))).replace("@L2@", str(sub.get("keyword_scale", 1.15))).replace("@CAP_WEIGHT@", "700" if bold else "500").replace("@CAP_STYLE@", "italic" if italic else "normal")
           .replace("@SHADOW_Y@", str(max(3, int(base_px * pre.get("shadow", 0.05))))).replace("@SHADOW_B@", str(max(6, int(base_px * 0.14))))
           .replace("@STROKE@", str(max(3, int(base_px * 0.09)))).replace("@BAR@", str(max(6, int(0.006 * H))))
           .replace("@DASH@", str(max(4, int(0.004 * H)))))

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
        elif t == "glass_badge":
            build_glass_badge(c, ov)
        elif t == "big_number":
            build_big_number(c, ov)
        elif t == "follow_cta":
            build_follow_cta(c, ov, project / "assets")
        elif t == "broll":
            build_broll(c, ov, project / "assets")
    if sub.get("enabled", True) and words:
        quiet = [(o["start"], o["start"] + o["duration"]) for o in overlays if o.get("type") == "numbered_title"]
        ws = [w for w in words if not any(a - 0.05 <= w["start"] < b for a, b in quiet)]
        build_captions(c, ws, sub, theme, base_px)

    zoom_js = ""
    if punch.get("enabled"):
        for a, b, z in sched:
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
