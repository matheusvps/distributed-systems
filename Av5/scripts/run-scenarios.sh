#!/usr/bin/env bash
# Launches the 4-node cluster, a logs window, and the interactive scenario client window.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

SKIP_BUILD=0
STARTUP_DELAY=0

usage() {
  cat <<EOF
uso: $(basename "$0") [opções]

  --skip-build       não executa docker compose build
  --startup SECONDS  pausa após 'up' antes de abrir janelas (padrão: $STARTUP_DELAY)
  -h, --help         esta ajuda

Abre duas janelas de terminal logo após subir os nós:
  1) logs dos 4 nós (docker compose logs -f) — acompanhe a eleição aqui
  2) driver interativo dos cenários 1–5 + modo livre

O Cenário 1 já pede para pressionar tecla quando o líder aparecer nos logs.

Requer um emulador de terminal: gnome-terminal, xfce4-terminal, konsole ou xterm.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --skip-build) SKIP_BUILD=1; shift ;;
    --startup) STARTUP_DELAY="${2:?}"; shift 2 ;;
    --wait) STARTUP_DELAY="${2:?}"; shift 2 ;;  # alias legado
    -h|--help) usage; exit 0 ;;
    *) echo "opção desconhecida: $1" >&2; usage; exit 1 ;;
  esac
done

open_terminal() {
  local title="$1"
  local cmd="$2"

  if command -v gnome-terminal &>/dev/null; then
    gnome-terminal --title="$title" -- bash -lc "$cmd"
  elif command -v xfce4-terminal &>/dev/null; then
    xfce4-terminal --title="$title" -e "bash -lc $(printf '%q' "$cmd")" &
  elif command -v konsole &>/dev/null; then
    konsole --new-tab -p tabtitle="$title" -e bash -lc "$cmd" &
  elif command -v xterm &>/dev/null; then
    xterm -title "$title" -e bash -lc "$cmd" &
  else
    echo "ERRO: nenhum terminal gráfico encontrado (gnome-terminal, xfce4-terminal, konsole, xterm)." >&2
    echo "Execute manualmente em dois terminais:" >&2
    echo "  docker compose logs -f node1 node2 node3 node4" >&2
    echo "  $ROOT/scripts/demo-client.sh" >&2
    exit 1
  fi
}

echo "==> Preparando ambiente em $ROOT"
mkdir -p data/node{1,2,3,4}
printf 'HOST_UID=%s\nHOST_GID=%s\n' "$(id -u)" "$(id -g)" > .env

if [[ "$SKIP_BUILD" -eq 0 ]]; then
  echo "==> docker compose build"
  docker compose build
fi

echo "==> Subindo nós (node1..node4)"
docker compose up -d node1 node2 node3 node4

if [[ "$STARTUP_DELAY" -gt 0 ]]; then
  echo "==> Aguardando ${STARTUP_DELAY}s (containers subindo)..."
  sleep "$STARTUP_DELAY"
fi

LOGS_CMD="cd $(printf '%q' "$ROOT") && echo '=== Av5 — logs dos nós (Ctrl+C para parar o follow) ===' && docker compose logs -f node1 node2 node3 node4; echo; echo '--- logs encerrados (digite exit para fechar) ---'; exec bash"
CLIENT_CMD="cd $(printf '%q' "$ROOT") && $(printf '%q' "$ROOT/scripts/demo-client.sh"); echo; echo '--- driver encerrado (digite exit para fechar a janela) ---'; exec bash"

echo "==> Abrindo janela de logs..."
open_terminal "Av5 — Logs" "$LOGS_CMD"

sleep 1

echo "==> Abrindo janela do cliente interativo..."
open_terminal "Av5 — Cliente" "$CLIENT_CMD"

echo
echo "Demonstração iniciada."
echo "  • Janela 'Av5 — Logs'    : acompanhe eleição, replicação e recuperação"
echo "  • Janela 'Av5 — Cliente' : pressione tecla entre cada passo dos cenários"
echo
echo "Para encerrar o cluster depois:"
echo "  cd $ROOT && docker compose down"
echo "  rm -rf data/   # opcional: limpar persistência"
