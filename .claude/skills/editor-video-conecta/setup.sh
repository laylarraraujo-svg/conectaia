#!/usr/bin/env bash
# Instala tudo que o editor de vídeo precisa: FFmpeg, Whisper, HyperFrames e a fonte Cal Sans.
set -e
DIR="$(cd "$(dirname "$0")" && pwd)"
command -v ffmpeg >/dev/null || { apt-get update -qq && apt-get install -y -qq ffmpeg; }
pip install -q faster-whisper matplotlib pillow opencv-python-headless "av>=11,<17" yt-dlp   # av 17+ quebra o faster-whisper
npm i -g -s hyperframes@0.8.209
mkdir -p /usr/local/share/fonts && cp "$DIR"/fonts/*.ttf /usr/local/share/fonts/ && fc-cache -f >/dev/null
# Chrome para o render: usa o Chromium do ambiente se existir
[ -x /opt/pw-browsers/chromium ] && echo 'export HYPERFRAMES_BROWSER_PATH=/opt/pw-browsers/chromium' >> ~/.bashrc
python3 -c "from faster_whisper import WhisperModel; WhisperModel('small', device='cpu', compute_type='int8')" && echo "Modelo Whisper pronto."
echo "Editor de vídeo instalado."
