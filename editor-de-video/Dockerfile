# Studio: editor de vídeo online. Imagem com Python, FFmpeg, Node 22 (HyperFrames) e Chromium.
FROM node:22-bookworm-slim

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    HF_HOME=/opt/whisper \
    HYPERFRAMES_BROWSER_PATH=/usr/bin/chromium \
    PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium \
    STUDIO_CONFIG=/dados/config \
    STUDIO_PROJETOS=/dados/projetos

RUN apt-get update && apt-get install -y --no-install-recommends \
      python3 python3-venv ffmpeg chromium fontconfig fonts-dejavu-core ca-certificates curl tini \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN python3 -m venv /opt/venv && pip install --no-cache-dir -r requirements.txt

# HyperFrames e GSAP ficam na imagem: o render não depende de baixar nada
RUN npm install -g hyperframes@0.8.209 --no-audit --no-fund \
    && mkdir -p /tmp/g && cd /tmp/g && npm pack gsap@3.14.2 --silent && tar xzf gsap-*.tgz \
    && mkdir -p /app/motor/vendor && cp package/dist/gsap.min.js /app/motor/vendor/ && rm -rf /tmp/g

# Modelo de transcrição (Whisper small, ~460 MB) já baixado
RUN python3 -c "from faster_whisper import WhisperModel; WhisperModel('small', device='cpu', compute_type='int8')"

COPY . .
# usuário sem privilégios (uid 1000, já existe na imagem do Node)
RUN mkdir -p /dados && chown -R node:node /dados /app /opt/whisper
USER node
# aquece o cache do npx (o render chama npx hyperframes@versão)
RUN cd /tmp && npx --yes hyperframes@0.8.209 --version >/dev/null 2>&1 || true

VOLUME ["/dados"]
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s CMD curl -fs http://127.0.0.1:8080/saude || exit 1
ENTRYPOINT ["/usr/bin/tini", "--", "/app/iniciar.sh"]
