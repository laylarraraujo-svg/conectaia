#!/bin/sh
# Ponto de partida do contêiner: prepara /dados na primeira vez e sobe o servidor.
set -e
mkdir -p "$STUDIO_CONFIG/modelos" "$STUDIO_CONFIG/musicas" "$STUDIO_PROJETOS"
if [ ! -f "$STUDIO_CONFIG/marca.json" ]; then
  cp /app/config/marca.exemplo.json "$STUDIO_CONFIG/marca.json"
  echo "Criado $STUDIO_CONFIG/marca.json: edite com o nome, cores e textos do cliente."
fi
exec python3 /app/web/servidor.py --publico --porta 8080
