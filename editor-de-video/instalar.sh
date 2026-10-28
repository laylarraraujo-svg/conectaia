#!/usr/bin/env bash
# Instala o Studio num servidor Linux (Ubuntu/Debian). Rode dentro da pasta editor-de-video:
#   sudo ./instalar.sh
# Pode rodar de novo para atualizar: mantém marca, usuários e vídeos (pasta dados/).
set -euo pipefail
cd "$(dirname "$0")"

verde() { printf '\033[32m%s\033[0m\n' "$*"; }
amarelo() { printf '\033[33m%s\033[0m\n' "$*"; }

if ! command -v docker >/dev/null 2>&1; then
  verde "Instalando o Docker..."
  curl -fsSL https://get.docker.com | sh
fi
docker compose version >/dev/null 2>&1 || { echo "Docker Compose não encontrado. Atualize o Docker."; exit 1; }

if [ ! -f .env ]; then
  verde "Configuração inicial"
  read -rp "Domínio (ex.: studio.cliente.com.br; Enter para testar pelo IP): " DOMINIO
  read -rp "E-mail do primeiro login: " EMAIL
  while true; do
    read -rsp "Senha (mín. 8 caracteres): " SENHA; echo
    [ ${#SENHA} -ge 8 ] && break
    amarelo "Senha curta demais."
  done
  MEM_KB=$(awk '/MemTotal/ {print $2}' /proc/meminfo)
  MEM=$(( MEM_KB / 1024 / 1024 * 3 / 4 )); [ "$MEM" -lt 2 ] && MEM=2
  HTTPS=0; [ -n "$DOMINIO" ] && HTTPS=1
  cat > .env <<EOF
DOMINIO=$DOMINIO
STUDIO_HTTPS=$HTTPS
STUDIO_MEMORIA=${MEM}g
EOF
  chmod 600 .env
fi

mkdir -p dados && chown -R 1000:1000 dados
verde "Construindo e subindo (a primeira vez leva alguns minutos)..."
docker compose up -d --build

verde "Aguardando o sistema ligar..."
for _ in $(seq 1 60); do
  docker compose exec -T studio curl -fs http://127.0.0.1:8080/saude >/dev/null 2>&1 && break
  sleep 2
done
# a senha vai direto para o sistema (fica só como hash); não é gravada no .env
if [ -n "${EMAIL:-}" ]; then
  docker compose exec -T -e NOVA_SENHA="$SENHA" studio python web/acesso.py adicionar "$EMAIL" Administrador
  unset SENHA
fi

. ./.env
IP=$(curl -fs4 https://ifconfig.me 2>/dev/null || hostname -I | awk '{print $1}')
echo
verde "Pronto!"
if [ -n "${DOMINIO:-}" ]; then
  echo "Acesse: https://$DOMINIO   (o DNS do domínio precisa apontar para $IP)"
else
  echo "Acesse: http://$IP   (sem HTTPS: use só para teste)"
fi
echo "Marca do cliente: edite dados/config/marca.json e coloque o logo em dados/config/ (depois: docker compose restart studio)"
echo "Novo usuário:     docker compose exec studio python web/acesso.py adicionar pessoa@cliente.com.br"
