"""Efeitos sonoros sintetizados (sem direitos autorais: gerados aqui com o FFmpeg) e sincronizados com as animações.

Sons: whoosh, pop, impacto, glitch, tique, ding.
eventos_de(overlays) decide onde entra cada som a partir dos tempos das animações; mixar() aplica no vídeo final.
"""
import subprocess
from pathlib import Path

SR = 48000
RECEITAS = {
    # entrada de elemento: ruído rosa filtrado com subida e descida
    "whoosh": ["-f", "lavfi", "-i", "anoisesrc=d=0.55:c=pink:a=0.9",
               "-af", "highpass=f=350,lowpass=f=5200,afade=t=in:st=0:d=0.28:curve=exp,afade=t=out:st=0.28:d=0.27,volume=1.6"],
    # ícone aparecendo: blip curto com queda de tom
    "pop": ["-f", "lavfi", "-i", "aevalsrc='0.9*sin(2*PI*(520+900*exp(-28*t))*t)*exp(-22*t)':s=48000:d=0.18"],
    # carimbo / número de impacto: grave + estalo
    "impacto": ["-f", "lavfi", "-i", "aevalsrc='0.95*sin(2*PI*52*t)*exp(-6*t)+0.6*sin(2*PI*104*t)*exp(-10*t)+0.35*(random(0)*2-1)*exp(-45*t)':s=48000:d=0.7",
                "-af", "lowpass=f=2400,volume=1.4"],
    # glitch: ruído com resolução reduzida e cortes rápidos
    "glitch": ["-f", "lavfi", "-i", "anoisesrc=d=0.38:c=white:a=0.5",
               "-af", "acrusher=bits=5:samples=24:mix=1,tremolo=f=28:d=1,highpass=f=600,afade=t=out:st=0.25:d=0.13,volume=0.9"],
    # X marcando: clique seco
    "tique": ["-f", "lavfi", "-i", "aevalsrc='0.8*sin(2*PI*1900*t)*exp(-70*t)+0.5*sin(2*PI*140*t)*exp(-40*t)':s=48000:d=0.12"],
    # cartão final: sino suave
    "ding": ["-f", "lavfi", "-i", "aevalsrc='0.45*sin(2*PI*1318.5*t)*exp(-3.2*t)+0.3*sin(2*PI*1975.5*t)*exp(-4.5*t)+0.15*sin(2*PI*2637*t)*exp(-6*t)':s=48000:d=1.6"],
}
VOLUME = {"whoosh": 0.8, "pop": 0.32, "impacto": 0.65, "glitch": 0.28, "tique": 0.4, "ding": 0.4}


def gerar_biblioteca(pasta):
    """Cria os .wav dos efeitos (uma vez) e devolve {nome: caminho}."""
    pasta = Path(pasta)
    pasta.mkdir(parents=True, exist_ok=True)
    out = {}
    for nome, args in RECEITAS.items():
        dst = pasta / f"{nome}.wav"
        if not dst.exists():
            subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", *args, "-ar", str(SR), "-ac", "2", str(dst)], check=True)
        out[nome] = dst
    return out


def eventos_de(overlays):
    """Lista de (tempo, som) a partir das animações do plano."""
    ev = []
    for o in overlays:
        t, s = o.get("type"), o.get("start", 0)
        if t == "alerta":
            ev += [(max(0, s - 0.05), "whoosh"), (s + 0.05, "pop")]
        elif t == "icones":
            ev += [(s, "whoosh")] if o.get("apagado") else [(s + 0.2 * k, "pop") for k in range(int(o.get("n", 3)))]
        elif t == "carimbo":
            for b in o.get("batidas", [s]):
                ev += [(b + 0.12, "impacto"), (b + 0.22, "glitch")]
        elif t == "palavra":
            ev += [(s, "whoosh")]
        elif t == "lista_x":
            ev += [(it.get("inicio", s), "tique") for it in o.get("itens", [])]
        elif t == "tentativas":
            ev += [(s + 0.12 * k, "pop") for k in range(int(o.get("n", 4)))]
            ev += [(m + 0.1, "tique") for m in o.get("marcas", [])]
            if o.get("rotulo_em"):
                ev += [(o["rotulo_em"], "impacto"), (o["rotulo_em"] + 0.3, "glitch")]
            if o.get("sub_em"):
                ev += [(o["sub_em"], "pop")]
        elif t == "faixas":
            ev += [(it.get("inicio", s), "whoosh") for it in o.get("itens", [])]
        elif t == "end_card":
            ev += [(max(0, s - 0.1), "whoosh"), (s + 0.45, "ding")]
        elif t in ("title", "recorte", "stat", "chart", "lower_third", "numbered_title", "cards", "steps", "pillars"):
            ev += [(s, "whoosh")]
    return sorted(ev)


def mixar(video, eventos, sons, out, ganho=1.0):
    """Soma os efeitos ao áudio do vídeo (que já tem voz e música). O vídeo é copiado sem recodificar."""
    if not eventos:
        return False
    args = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(video)]
    grafo = []
    for k, (t, nome) in enumerate(eventos):
        args += ["-i", str(sons[nome])]
        ms = max(0, int(t * 1000))
        grafo.append(f"[{k + 1}:a]volume={VOLUME[nome] * ganho:.3f},adelay={ms}|{ms}[e{k}]")
    entradas = "".join(f"[e{k}]" for k in range(len(eventos)))
    grafo.append(f"[0:a]{entradas}amix=inputs={len(eventos) + 1}:duration=first:normalize=0,alimiter=limit=0.95[a]")
    args += ["-filter_complex", ";".join(grafo), "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
             "-movflags", "+faststart", str(out)]
    subprocess.run(args, check=True)
    return True
