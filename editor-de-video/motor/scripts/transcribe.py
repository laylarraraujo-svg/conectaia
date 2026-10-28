#!/usr/bin/env python3
"""Transcreve um vídeo/áudio com Whisper local (faster-whisper), com tempo por palavra.

Saída (JSON): {"language": "pt", "duration": 83.2, "words": [{"start": 0.31, "end": 0.62, "word": "Olá"}, ...]}

Uso:
  python transcribe.py video.mp4 -o transcript.json [--model small] [--language pt]
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import probe, require_ffmpeg, save_json


def transcribe(path, model="small", language="pt", initial_prompt=None, device="auto"):
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        sys.exit("faster-whisper não instalado. Rode: pip install faster-whisper")

    import subprocess
    import numpy as np
    # decodifica com o FFmpeg (16 kHz mono): evita depender da versão do PyAV usada pelo faster-whisper
    pcm = subprocess.run(["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-i", str(path), "-vn", "-ac", "1",
                          "-ar", "16000", "-f", "s16le", "-"], capture_output=True, check=True).stdout
    audio = np.frombuffer(pcm, np.int16).astype(np.float32) / 32768.0

    compute = "int8" if device in ("auto", "cpu") else "float16"
    wm = WhisperModel(model, device=device, compute_type=compute)
    segments, info = wm.transcribe(
        audio,
        language=None if language in (None, "auto") else language,
        word_timestamps=True,
        vad_filter=True,                     # ignora trechos sem fala: menos alucinação
        vad_parameters={"min_silence_duration_ms": 300},
        initial_prompt=initial_prompt,       # útil para nomes próprios e termos técnicos
        condition_on_previous_text=False,
    )
    words = []
    for seg in segments:
        for w in seg.words or []:
            text = w.word.strip()
            if text:
                words.append({"start": round(w.start, 3), "end": round(w.end, 3), "word": text})
    return {"language": info.language, "duration": round(info.duration, 3), "words": words}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input")
    ap.add_argument("-o", "--output", default=None)
    ap.add_argument("--model", default="small", help="tiny, base, small (padrão), medium, large-v3")
    ap.add_argument("--language", default="pt", help="código do idioma ou 'auto'")
    ap.add_argument("--prompt", default=None, help="vocabulário/nomes para ajudar o Whisper")
    ap.add_argument("--device", default="auto", help="auto, cpu ou cuda")
    args = ap.parse_args()

    require_ffmpeg()
    out = Path(args.output or Path(args.input).with_suffix(".transcript.json"))
    data = transcribe(args.input, args.model, args.language, args.prompt, args.device)
    save_json(data, out)
    print(f"{len(data['words'])} palavras -> {out}")


if __name__ == "__main__":
    main()
