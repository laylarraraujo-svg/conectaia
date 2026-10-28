#!/usr/bin/env python3
"""Gera um arquivo .ass (legendas animadas + títulos + lower thirds) a partir do transcript.

Uso (só legendas):
  python build_ass.py transcript.json -o legendas.ass --width 1080 --height 1920 [--style viral]

Estilos de legenda: viral (palavra ativa colorida, caixa alta), clean (frase limpa), box (fundo escuro).
"""
import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import ass_time, hex_to_ass, hex_to_ass_c, load_json, pick_font, text_width

DEFAULT_THEME = {"accent": "#FFD60A", "text": "#FFFFFF", "card": "#111827"}

SUB_PRESETS = {
    #            palavras  caixa-alta  destaca  BorderStyle  contorno(% do corpo)
    "viral": {"max_words": 3, "upper": True,  "highlight": True,  "border": 1, "outline": 0.10, "bold": True},
    "clean": {"max_words": 7, "upper": False, "highlight": False, "border": 1, "outline": 0.06, "bold": True},
    "box":   {"max_words": 4, "upper": False, "highlight": True,  "border": 3, "outline": 0.22, "bold": True},
    # estilo do Reel de referência: 2-3 palavras, centro do quadro, sombra suave, palavra-chave amarela na 2ª linha
    "ref":   {"max_words": 3, "upper": False, "highlight": False, "border": 1, "outline": 0.0, "bold": True,
              "italic": True, "shadow": 0.07, "stack": True, "pos_y": 0.53, "max_chars": 17},
}

EMPH_RE = re.compile(r"[0-9$%]|R\$")


def is_emphasis(word, opts):
    """Palavra-chave: marcada com *asteriscos*, na lista highlight_words, número/moeda, ou comprida (auto_long)."""
    w = word.strip(".,!?;:").lower()
    if word.startswith("*") and word.rstrip(".,!?;:").endswith("*"):
        return True
    if w in {x.lower() for x in opts.get("highlight_words", [])}:
        return True
    if EMPH_RE.search(w):
        return True
    return len(w) >= opts.get("auto_long", 0) > 0


def stack_events(groups, W, H, opts, theme, preset):
    """Cada grupo vira 1 evento; palavras-chave finais vão para uma 2ª linha maior, amarela e em caixa alta."""
    acc = hex_to_ass_c(opts.get("highlight_color", theme["accent"]))
    base = preset.get("size_px") or int(opts.get("size") or 0.052 * H)
    y = int(opts.get("pos_y", preset["pos_y"]) * H)
    events = []
    for gi, g in enumerate(groups):
        words = [(w["word"].strip("*"), is_emphasis(w["word"], opts)) for w in g]
        k = len(words)
        while k > 0 and words[k - 1][1]:
            k -= 1                                      # k = início do bloco final de palavras-chave
        plain, key = words[:k], words[k:]
        if key and not plain:                           # grupo todo em destaque: fica em linha única
            line = f"{{\\c{acc}\\fs{int(base * 1.15)}}}" + _esc(" ".join(t for t, _ in key)).upper()
        elif key:
            line = (f"{_esc(' '.join(t for t, _ in plain))}\\N"
                    f"{{\\c{acc}\\fs{int(base * 1.15)}}}{_esc(' '.join(t for t, _ in key)).upper()}")
        else:
            inline = [(f"{{\\c{acc}}}{_esc(t)}{{\\r}}" if e else _esc(t)) for t, e in words]
            line = " ".join(inline)
        start = g[0]["start"]
        end = g[-1]["end"] + 0.2
        if gi + 1 < len(groups):
            end = min(end, groups[gi + 1][0]["start"])
        end = max(end, start + 0.15)
        tags = (f"{{\\an5\\pos({W // 2},{y})\\fscx85\\fscy85\\t(0,120,\\fscx100\\fscy100)\\shad{max(2, int(base * preset['shadow']))}}}")
        events.append(f"Dialogue: 0,{ass_time(start)},{ass_time(end)},Sub,,0,0,0,,{tags}{line}")
    return events


def _esc(text):
    return text.replace("\\", "").replace("{", "(").replace("}", ")").replace("\n", " ")


def group_words(words, max_words, max_chars=22, gap=0.55):
    """Agrupa palavras em blocos curtos: quebra por limite, pausa ou pontuação final."""
    groups, cur = [], []
    for w in words:
        if cur:
            too_long = len(" ".join(x["word"] for x in cur + [w])) > max_chars
            pause = w["start"] - cur[-1]["end"] > gap
            ended = re.search(r"[.!?…]$", cur[-1]["word"])
            if len(cur) >= max_words or too_long or pause or ended:
                groups.append(cur)
                cur = []
        cur.append(w)
    if cur:
        groups.append(cur)
    return groups


def subtitle_events(words, W, H, opts, theme):
    preset = {**SUB_PRESETS.get(opts.get("style", "viral"), SUB_PRESETS["viral"])}
    for k in ("max_words", "upper"):
        if opts.get(k) is not None:
            preset[k] = opts[k]
    acc = hex_to_ass_c(opts.get("highlight_color", theme["accent"]))
    groups = group_words(words, preset["max_words"],
                         max_chars=opts.get("max_chars", preset.get("max_chars", 22 if W < H else 42)))
    if preset.get("stack"):
        return stack_events(groups, W, H, {**opts, "pos_y": opts.get("pos_y", preset["pos_y"])}, theme, preset)
    events = []
    for gi, g in enumerate(groups):
        texts = [(_esc(w["word"]).upper() if preset["upper"] else _esc(w["word"])) for w in g]
        next_start = groups[gi + 1][0]["start"] if gi + 1 < len(groups) else None
        for j, w in enumerate(g):
            start = w["start"] if j > 0 else g[0]["start"]
            if j + 1 < len(g):
                end = g[j + 1]["start"]
            else:
                end = w["end"] + 0.25
                if next_start is not None:
                    end = min(end, next_start)
            end = max(end, start + 0.08)
            if preset["highlight"]:
                parts = [(f"{{\\c{acc}}}{t}{{\\r}}" if k == j else t) for k, t in enumerate(texts)]
            else:
                parts = texts
            line = " ".join(parts)
            if j == 0:                               # "pop" de entrada do bloco
                line = "{\\fscx88\\fscy88\\t(0,110,\\fscx100\\fscy100)}" + line
            events.append(f"Dialogue: 0,{ass_time(start)},{ass_time(end)},Sub,,0,0,0,,{line}")
    return events


def overlay_events(overlays, W, H, theme, font):
    """Eventos ASS para overlays de texto: type = title | lower_third."""
    events, acc, base = [], hex_to_ass_c(theme["accent"]), hex_to_ass_c(theme["text"])
    vertical = W < H
    for ov in overlays:
        kind = ov.get("type")
        s, e = ov["start"], ov["start"] + ov["duration"]
        if kind == "title":
            pos = ov.get("position", "top")
            y = {"top": 0.13, "center": 0.5, "bottom": 0.78}.get(pos, 0.13) * H
            an = 8 if pos != "center" else 5
            x = W / 2
            text = re.sub(r"\*(.+?)\*", lambda m: f"{{\\c{acc}}}{_esc(m.group(1))}{{\\c{base}}}", ov["text"])
            text = text if "{\\c" in text else _esc(text)
            events.append(
                f"Dialogue: 2,{ass_time(s)},{ass_time(e)},Title,,0,0,0,,"
                f"{{\\an{an}\\fad(250,250)\\move({x:.0f},{y + 0.03 * H:.0f},{x:.0f},{y:.0f},0,320)}}{text}")
        elif kind == "numbered_title":
            # título de lista: numeral amarelo grande + texto branco em caixa alta, com "pop" de entrada
            y = ov.get("y", 0.52) * H
            big, med = int(0.095 * H), int(0.062 * H)
            line = (f"{{\\c{acc}\\fs{big}}}{_esc(str(ov['number']))}{{\\c{base}\\fs{med}}}  "
                    f"{_esc(ov['text']).upper()}")
            events.append(f"Dialogue: 2,{ass_time(s)},{ass_time(e)},Title,,0,0,0,,"
                          f"{{\\an5\\pos({W // 2},{y:.0f})\\fad(120,200)\\fscx70\\fscy70\\t(0,180,\\fscx108\\fscy108)"
                          f"\\t(180,300,\\fscx100\\fscy100)}}{line}")
        elif kind == "lower_third":
            size_t, size_s = int(0.036 * H if vertical else 0.052 * H), int(0.026 * H if vertical else 0.036 * H)
            pad, bar = int(0.012 * H), max(6, int(0.006 * H))
            tw = max(text_width(ov["title"], size_t, font), text_width(ov.get("subtitle", ""), size_s, font, False))
            cw, ch = int(tw + 2 * pad + bar + 10), int(size_t + (size_s * 1.25 if ov.get("subtitle") else 0) + 2 * pad)
            x = int(0.06 * W)
            y = int(ov.get("y", 0.58 if vertical else 0.70) * H)
            mv = lambda dx=0: f"\\move({x - 0.12 * W:.0f},{y + dx},{x},{y + dx},0,350)"
            fade = "\\fad(300,300)"
            card = f"m 0 0 l {cw} 0 l {cw} {ch} l 0 {ch}"
            barp = f"m 0 0 l {bar} 0 l {bar} {ch} l 0 {ch}"
            events.append(f"Dialogue: 1,{ass_time(s)},{ass_time(e)},Card,,0,0,0,,"
                          f"{{\\an7{mv()}{fade}\\p1\\c{hex_to_ass_c(theme['card'])}\\1a&H30&}}{card}")
            events.append(f"Dialogue: 2,{ass_time(s)},{ass_time(e)},Card,,0,0,0,,"
                          f"{{\\an7{mv()}{fade}\\p1\\c{acc}}}{barp}")
            tx = x + bar + pad
            events.append(f"Dialogue: 3,{ass_time(s)},{ass_time(e)},LT1,,0,0,0,,"
                          f"{{\\an7\\move({tx - 0.12 * W:.0f},{y + pad},{tx},{y + pad},0,350){fade}}}{_esc(ov['title'])}")
            if ov.get("subtitle"):
                ys = y + pad + int(size_t * 1.12)
                events.append(f"Dialogue: 3,{ass_time(s)},{ass_time(e)},LT2,,0,0,0,,"
                              f"{{\\an7\\move({x - 0.12 * W + bar + pad:.0f},{ys},{x + bar + pad},{ys},0,350){fade}}}"
                              f"{_esc(ov['subtitle'])}")
    return events


def build_ass(words, W, H, opts=None, overlays=None, theme=None, font=None):
    opts, overlays = opts or {}, overlays or []
    theme = {**DEFAULT_THEME, **(theme or {})}
    font = pick_font(font or opts.get("font"))
    vertical = W < H
    preset = {**SUB_PRESETS.get(opts.get("style", "viral"), SUB_PRESETS["viral"])}
    for k in ("bold", "italic"):
        if opts.get(k) is not None:
            preset[k] = opts[k]
    size = int(opts.get("size") or (0.052 * H if vertical else 0.062 * H))
    pos = opts.get("position", "bottom")
    # margens: vertical deixa a legenda mais alta para fugir da UI do Reels/TikTok
    mv = int(opts.get("margin_v", {"bottom": (0.22 if vertical else 0.08) * H,
                                    "center": 0, "top": 0.12 * H}[pos]))
    align = {"bottom": 2, "center": 5, "top": 8}[pos]
    outline = int(size * preset["outline"]) if preset["outline"] == 0 else max(2, int(size * preset["outline"]))
    back = hex_to_ass(theme["card"], 0x40) if preset["border"] == 3 else ("&H70000000" if preset.get("shadow") else "&H80000000")
    outc = hex_to_ass(theme["card"], 0x30) if preset["border"] == 3 else "&H00000000"
    size_t, size_s = int(0.062 * H if vertical else 0.07 * H), int(0.026 * H if vertical else 0.036 * H)
    styles = [
        f"Style: Sub,{font},{size},{hex_to_ass(theme['text'])},&H000000FF,{outc},{back},"
        f"{-1 if preset['bold'] else 0},{-1 if preset.get('italic') else 0},0,0,100,100,0,0,{preset['border']},{outline},{max(2, int(size * preset.get('shadow', 0)))},{align},{int(0.06 * W)},{int(0.06 * W)},{mv},1",
        f"Style: Title,{font},{size_t},{hex_to_ass(theme['text'])},&H000000FF,&H00000000,&H70000000,-1,-1,0,0,100,100,0,0,1,0,{max(3, int(size_t * 0.08))},8,{int(0.08 * W)},{int(0.08 * W)},0,1",
        f"Style: LT1,{font},{int(0.036 * H if vertical else 0.052 * H)},{hex_to_ass(theme['text'])},&H000000FF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1",
        f"Style: LT2,{font},{size_s},{hex_to_ass('#D1D5DB')},&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1",
        f"Style: Card,{font},20,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1",
    ]
    header = (
        "[Script Info]\nScriptType: v4.00+\nWrapStyle: 0\nScaledBorderAndShadow: yes\n"
        f"PlayResX: {W}\nPlayResY: {H}\n\n[V4+ Styles]\n"
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, "
        "Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, "
        "MarginV, Encoding\n" + "\n".join(styles) +
        "\n\n[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")
    events = []
    if words and opts.get("enabled", True) is not False:
        quiet = [(o["start"], o["start"] + o["duration"]) for o in overlays if o.get("type") == "numbered_title"]
        words = [w for w in words if not any(a - 0.05 <= w["start"] < b for a, b in quiet)]
        events += subtitle_events(words, W, H, opts, theme)
    events += overlay_events([o for o in overlays if o.get("type") in ("title", "lower_third", "numbered_title")], W, H, theme, font)
    return header + "\n".join(events) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("transcript")
    ap.add_argument("-o", "--output", required=True)
    ap.add_argument("--width", type=int, default=1080)
    ap.add_argument("--height", type=int, default=1920)
    ap.add_argument("--style", default="viral", choices=list(SUB_PRESETS))
    ap.add_argument("--position", default="bottom", choices=["bottom", "center", "top"])
    ap.add_argument("--font", default=None)
    args = ap.parse_args()
    words = load_json(args.transcript)["words"]
    ass = build_ass(words, args.width, args.height, {"style": args.style, "position": args.position, "font": args.font})
    Path(args.output).write_text(ass, encoding="utf-8")
    print(f"legendas -> {args.output}")


if __name__ == "__main__":
    main()
