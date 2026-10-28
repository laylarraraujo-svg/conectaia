#!/usr/bin/env python3
"""Renderiza gráficos animados (barras, linha, número em contagem) como sequência de PNGs com transparência.

O edit_video.py sobrepõe essas sequências no vídeo. Uso isolado (para pré-visualizar um gráfico):
  python charts.py spec_do_grafico.json -o pasta_saida --width 1080 --height 1920
"""
import argparse
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager as fm
from matplotlib.patches import Circle, FancyBboxPatch, Polygon

sys.path.insert(0, str(Path(__file__).parent))
from common import font_path, load_json, pick_font

THEME = {"accent": "#FFD60A", "text": "#FFFFFF", "card": "#111827", "muted": "#6B7280"}
ANIM_SECONDS = 1.3


def ease(x):
    x = min(1.0, max(0.0, x))
    return 1 - (1 - x) ** 3


def fmt_num(v, decimals=0, prefix="", suffix=""):
    """Formato brasileiro: 1.234,5"""
    s = f"{v:,.{decimals}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{prefix}{s}{suffix}"


def chart_size(kind, W, H):
    vertical = W < H
    if kind == "pillars":                                   # tela cheia
        return W // 2 * 2, H // 2 * 2
    if kind == "steps":
        return int(0.74 * W) // 2 * 2, int(0.13 * H) // 2 * 2
    if kind == "cards":
        return int(0.92 * W) // 2 * 2, int(0.16 * H) // 2 * 2
    if kind == "stat":
        cw, ch = (0.62 * W, 0.15 * H) if vertical else (0.28 * W, 0.24 * H)
    else:
        cw, ch = (0.88 * W, 0.27 * H) if vertical else (0.44 * W, 0.44 * H)
    return int(cw) // 2 * 2, int(ch) // 2 * 2


def _fonts(family):
    path = font_path(family, True)
    if path:
        fm.fontManager.addfont(path)
        name = fm.FontProperties(fname=path).get_name()
        plt.rcParams["font.family"] = name


def _card(fig, cw, ch, theme):
    bg = fig.add_axes([0, 0, 1, 1])
    bg.set_xlim(0, cw); bg.set_ylim(0, ch); bg.axis("off")
    r = 0.07 * min(cw, ch)
    bg.add_patch(FancyBboxPatch((2, 2), cw - 4, ch - 4, boxstyle=f"round,pad=0,rounding_size={r}",
                                fc=theme["card"], ec="none", alpha=0.90))
    return bg


def _style_axes(ax, theme):
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(theme["muted"])
    ax.tick_params(colors=theme["text"], length=0)
    ax.set_yticks([])


def pop(t, start=0.0, span=0.35):
    """0 -> 1.12 -> 1 (efeito 'pop' de entrada)."""
    x = min(1.0, max(0.0, (t - start) / span))
    return 0.0 if x <= 0 else (1.12 * ease(x / 0.7) if x < 0.7 else 1.12 - 0.12 * ease((x - 0.7) / 0.3))


def _blank(fig, cw, ch):
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, cw); ax.set_ylim(0, ch); ax.axis("off")
    ax.set_aspect("auto")
    return ax


def draw_steps(spec, t, cw, ch, fig, theme):
    """Círculos numerados 1-2-3; o ativo ganha anel tracejado amarelo."""
    ax = _blank(fig, cw, ch)
    n, active = int(spec.get("count", 3)), int(spec.get("active", 1))
    r = ch * 0.40
    for i in range(n):
        cx = cw * (i + 0.5) / n
        on = (i + 1) == active
        sc = pop(t, 0.0 if on else 0.0 + 0.05 * i, 0.5) if on or spec.get("show_all", True) else 0
        if sc <= 0:
            continue
        ax.add_patch(Circle((cx, ch / 2), r * sc, fc="#0B0B10", ec="none", alpha=0.62))
        ax.add_patch(Circle((cx, ch / 2), r * sc, fc="none", ec=theme["accent"] if on else theme["muted"],
                            lw=ch * 0.045 * 72 / 100, ls=(0, (2.2, 1.6)) if on else "-", alpha=1 if on else 0.55))
        ax.text(cx, ch / 2, str(i + 1), ha="center", va="center", color=theme["text"] if on else theme["muted"],
                fontsize=r * sc * 1.25 * 72 / 100, fontweight="bold", style="italic")


def draw_cards(spec, t, cw, ch, fig, theme):
    """Cartões quadrados com borda tracejada amarela que surgem em sequência (texto curto ou imagem)."""
    ax = _blank(fig, cw, ch)
    items = spec["items"]; n = len(items)
    side = min(ch * 0.86, cw / (n * 1.25))
    gap = side * 0.22
    x0 = (cw - (n * side + (n - 1) * gap)) / 2
    for i, it in enumerate(items):
        sc = pop(t, i * 0.18, 0.35)
        if sc <= 0:
            continue
        cx, cy = x0 + i * (side + gap) + side / 2, ch / 2
        w = side * sc
        ax.add_patch(FancyBboxPatch((cx - w / 2, cy - w / 2), w, w, boxstyle=f"round,pad=0,rounding_size={w * 0.16}",
                                    fc="#0B0B10", ec=theme["accent"], lw=side * 0.035 * 72 / 100, ls=(0, (2.4, 1.6)), alpha=0.85))
        if it.get("image"):
            img = plt.imread(it["image"])
            ax.imshow(img, extent=[cx - w * 0.36, cx + w * 0.36, cy - w * 0.36, cy + w * 0.36], zorder=5)
            ax.set_xlim(0, cw); ax.set_ylim(0, ch); ax.set_aspect("auto")
        else:
            ax.text(cx, cy, it.get("text", ""), ha="center", va="center", color=theme["text"],
                    fontsize=w * 0.22 * 72 / 100, fontweight="bold", zorder=6)


def draw_pillars(spec, t, cw, ch, fig, theme):
    """Ranking em pilares 3D sobre fundo escuro, tela cheia (como o gráfico 'Richest Companies' do Reel)."""
    ax = _blank(fig, cw, ch)
    grad = np.linspace(0, 1, 256).reshape(-1, 1)
    top, bot = np.array([0x0A, 0x0A, 0x0F]) / 255, np.array([0x1E, 0x1E, 0x28]) / 255
    img = top + (bot - top) * grad[:, :, None]
    ax.imshow(img, extent=[0, cw, 0, ch], aspect="auto", zorder=0)
    ax.set_xlim(0, cw); ax.set_ylim(0, ch)
    fs = ch * 0.034 * 72 / 100
    ax.text(cw / 2, ch * 0.78, spec.get("title", ""), ha="center", va="center", color=theme["accent"],
            fontsize=fs, fontweight="bold", zorder=5)
    if spec.get("subtitle"):
        ax.text(cw / 2, ch * 0.745, spec["subtitle"], ha="center", va="center", color=theme["text"],
                fontsize=fs * 0.9, fontweight="bold", zorder=5)
    labels, values = spec["labels"], [float(v) for v in spec["values"]]
    colors = spec.get("colors") or [theme["accent"]] * len(values)
    n = len(values); mx = max(values)
    bw = cw / (n * 1.7); dx, dy = bw * 0.32, bw * 0.2
    base_y = ch * 0.16
    order = sorted(range(n), key=lambda i: values[i])       # os maiores ficam à frente? não: desenha os menores por último
    for i in range(n):
        p = ease((t - 0.35 * i / max(n - 1, 1)) / 0.65)
        x = cw * (i + 0.5) / n - bw / 2
        h = (0.20 + 0.30 * values[i] / mx) * ch * p
        c = np.array(matplotlib.colors.to_rgb(colors[i]))
        ax.add_patch(Polygon([(x, base_y), (x + bw, base_y), (x + bw, base_y + h), (x, base_y + h)],
                             fc=c, ec="none", zorder=3))
        ax.add_patch(Polygon([(x, base_y + h), (x + bw, base_y + h), (x + bw + dx, base_y + h + dy), (x + dx, base_y + h + dy)],
                             fc=np.clip(c * 1.25 + 0.08, 0, 1), ec="none", zorder=3))
        ax.add_patch(Polygon([(x + bw, base_y), (x + bw + dx, base_y + dy), (x + bw + dx, base_y + h + dy), (x + bw, base_y + h)],
                             fc=c * 0.65, ec="none", zorder=3))
        if spec.get("logos") and spec["logos"][i]:
            lg = plt.imread(spec["logos"][i]); s_ = bw * 0.55
            ax.imshow(lg, extent=[x + bw / 2 - s_ / 2, x + bw / 2 + s_ / 2, base_y + h * 0.82 - s_ / 2, base_y + h * 0.82 + s_ / 2], zorder=6)
            ax.set_xlim(0, cw); ax.set_ylim(0, ch); ax.set_aspect("auto")
        ax.text(x + bw / 2, base_y - ch * 0.03, labels[i], ha="center", va="top", color=theme["text"],
                fontsize=ch * 0.016 * 72 / 100, fontweight="bold", alpha=min(1, p * 2), zorder=6)
        ax.text(x + bw / 2, base_y + h + dy + ch * 0.012, fmt_num(values[i] * p, int(spec.get("decimals", 0)),
                spec.get("prefix", ""), spec.get("suffix", "")), ha="center", va="bottom", color=theme["text"],
                fontsize=ch * 0.016 * 72 / 100, fontweight="bold", alpha=min(1, p * 2), zorder=6)


def draw_frame(spec, t, cw, ch, dpi, theme, path):
    """t em [0,1] = progresso da animação."""
    fig = plt.figure(figsize=(cw / dpi, ch / dpi), dpi=dpi)
    fig.patch.set_alpha(0)
    kind = spec.get("kind", "bar")
    if kind in ("steps", "cards", "pillars"):
        {"steps": draw_steps, "cards": draw_cards, "pillars": draw_pillars}[kind](spec, t, cw, ch, fig, theme)
        fig.savefig(path, dpi=dpi, transparent=True)
        plt.close(fig)
        return
    _card(fig, cw, ch, theme)
    title, px = spec.get("title", ""), ch / dpi * 72 / 72
    unit_pre, unit_suf, dec = spec.get("prefix", ""), spec.get("suffix", ""), int(spec.get("decimals", 0))
    fs_title, fs_label = ch * 0.085 * 72 / dpi, ch * 0.062 * 72 / dpi

    if kind == "stat":
        value = float(spec["value"]) * ease(t)
        fig.text(0.5, 0.60, fmt_num(value, dec, unit_pre, unit_suf), ha="center", va="center",
                 color=theme["accent"], fontsize=ch * 0.36 * 72 / dpi, fontweight="bold")
        fig.text(0.5, 0.20, spec.get("label", title), ha="center", va="center",
                 color=theme["text"], fontsize=ch * 0.12 * 72 / dpi)
    else:
        if title:
            fig.text(0.05, 0.89, title, ha="left", va="center", color=theme["text"],
                     fontsize=fs_title, fontweight="bold")
        ax = fig.add_axes([0.07, 0.17, 0.88, 0.56])
        ax.patch.set_alpha(0)
        _style_axes(ax, theme)
        labels, values = spec["labels"], [float(v) for v in spec["values"]]
        n = len(values)
        if kind == "bar":
            hi = spec.get("highlight", "max")
            hi_idx = values.index(max(values)) if hi == "max" else (n - 1 if hi == "last" else hi if isinstance(hi, int) else None)
            for i, v in enumerate(values):
                d = 0.4 * i / max(n - 1, 1)
                p = ease((t - d) / 0.6)
                color = theme["accent"] if (hi_idx is None or i == hi_idx) else theme["muted"]
                ax.bar(i, v * p, color=color, width=0.62)
                ax.text(i, v * p + max(values) * 0.03, fmt_num(v * p, dec, unit_pre, unit_suf), ha="center",
                        va="bottom", color=theme["text"], fontsize=fs_label, fontweight="bold",
                        alpha=min(1, p * 1.5))
            ax.set_ylim(0, max(values) * 1.28)
            ax.set_xlim(-0.6, n - 0.4)
            ax.set_xticks(range(n)); ax.set_xticklabels(labels, fontsize=fs_label)
        else:  # linha
            pos = ease(t) * (n - 1)
            xs, ys = list(range(n)), values
            k = int(pos)
            px_, py_ = xs[:k + 1], ys[:k + 1]
            if k < n - 1:
                f = pos - k
                px_ = px_ + [k + f]; py_ = py_ + [ys[k] + (ys[k + 1] - ys[k]) * f]
            ax.plot(px_, py_, color=theme["accent"], linewidth=ch * 0.012, solid_capstyle="round")
            ax.fill_between(px_, py_, min(values) - (max(values) - min(values)) * 0.2, color=theme["accent"], alpha=0.14)
            ax.scatter([px_[-1]], [py_[-1]], s=ch * 0.45, color=theme["accent"], zorder=5)
            ax.text(px_[-1], py_[-1] + (max(values) - min(values)) * 0.12, fmt_num(py_[-1], dec, unit_pre, unit_suf),
                    ha="center", va="bottom", color=theme["text"], fontsize=fs_label, fontweight="bold")
            rng = (max(values) - min(values)) or 1
            ax.set_ylim(min(values) - rng * 0.2, max(values) + rng * 0.45)
            ax.set_xlim(-0.3, n - 0.7)
            ax.set_xticks(range(n)); ax.set_xticklabels(labels, fontsize=fs_label)
    fig.savefig(path, dpi=dpi, transparent=True)
    plt.close(fig)


def render_chart(spec, W, H, outdir, theme=None, fps=30, font=None):
    """Gera os quadros e devolve metadados para o ffmpeg."""
    theme = {**THEME, **(theme or {})}
    _fonts(pick_font(font))
    outdir = Path(outdir); outdir.mkdir(parents=True, exist_ok=True)
    cw, ch = chart_size(spec.get("kind", "bar"), W, H)
    n = max(2, int(ANIM_SECONDS * fps))
    for i in range(n):
        draw_frame(spec, i / (n - 1), cw, ch, 100, theme, outdir / f"{i:04d}.png")
    return {"dir": str(outdir), "frames": n, "w": cw, "h": ch, "fps": fps, "anim": n / fps}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spec")
    ap.add_argument("-o", "--outdir", required=True)
    ap.add_argument("--width", type=int, default=1080)
    ap.add_argument("--height", type=int, default=1920)
    a = ap.parse_args()
    print(render_chart(load_json(a.spec), a.width, a.height, a.outdir))


if __name__ == "__main__":
    main()
