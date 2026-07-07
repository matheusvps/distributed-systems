#!/usr/bin/env bash
# Interactive scenario driver - runs queued client/ops steps; then free-form commands.
set -uo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

# shellcheck disable=SC2034
BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

pause_key() {
  local msg="${1:-Pressione qualquer tecla para o próximo passo... }"
  echo -e "${YELLOW}${msg}${NC}"
  read -n 1 -s -r _
  echo
}

run_client() {
  echo -e "${CYAN}\$ docker compose run --rm --no-deps client $*${NC}"
  if ! docker compose run --rm --no-deps client "$@"; then
    echo -e "${YELLOW}AVISO: comando do cliente falhou (código $?)${NC}" >&2
    return 1
  fi
}

dc() {
  echo -e "${CYAN}\$ docker compose $*${NC}"
  if ! docker compose "$@"; then
    echo -e "${YELLOW}AVISO: docker compose falhou (código $?)${NC}" >&2
    return 1
  fi
}

get_committed_index() {
  local node="${1:-}"
  local args=(consume)
  [[ -n "$node" ]] && args+=(--node "$node")
  local out
  if ! out=$(docker compose run --rm --no-deps client "${args[@]}" 2>&1); then
    return 1
  fi
  echo "$out" | grep -oE 'committed_index=[0-9]+' | head -1 | cut -d= -f2
}

get_leader_committed_index() {
  local max=0 idx
  for n in 1 2 3; do
    idx=$(get_committed_index "node${n}:600${n}") || continue
    if [[ "$idx" -gt "$max" ]]; then
      max=$idx
    fi
  done
  echo "$max"
}

# Descobre o ID do nó líder consultando cada nó (o cliente imprime "[lider]").
find_leader_id() {
  local n out
  for n in 1 2 3 4; do
    out=$(docker compose run --rm --no-deps client consume --node "node${n}:600${n}" 2>/dev/null) || continue
    if echo "$out" | grep -qi '^\[lider\]'; then
      echo "$n"
      return 0
    fi
  done
  return 1
}

# Escolhe uma réplica (não-líder) para o Cenário 4; prefere o maior ID disponível.
pick_replica_id() {
  local leader="$1" n
  for n in 4 3 2 1; do
    [[ "$n" == "$leader" ]] && continue
    echo "$n"
    return 0
  done
}

publish_and_get_index() {
  echo -e "${CYAN}\$ docker compose run --rm --no-deps client publish $*${NC}" >&2
  local out index
  if ! out=$(docker compose run --rm --no-deps client publish "$@" 2>&1); then
    echo "$out" >&2
    echo -e "${YELLOW}AVISO: publish falhou (código $?)${NC}" >&2
    return 1
  fi
  echo "$out" >&2
  index=$(echo "$out" | grep -oE 'index=[0-9]+' | tail -1 | cut -d= -f2)
  echo "$index"
}

wait_for_replica_sync() {
  local nid="$1"
  local target="${2:-0}"
  local timeout="${3:-90}"
  local addr="node${nid}:600${nid}"
  local elapsed=0 replica

  if [[ -z "$target" || "$target" -eq 0 ]]; then
    target=$(get_leader_committed_index)
  fi
  if [[ -z "$target" || "$target" -eq 0 ]]; then
    echo -e "${YELLOW}AVISO: não foi possível determinar índice alvo para sync${NC}" >&2
    return 1
  fi

  echo -e "${GREEN}Aguardando node${nid} sincronizar (alvo: committed_index>=${target})...${NC}"
  while [[ "$elapsed" -lt "$timeout" ]]; do
    replica=$(get_committed_index "$addr" || true)
    if [[ -n "$replica" && "$replica" -ge "$target" ]]; then
      echo -e "${GREEN}node${nid} sincronizado (committed_index=${replica})${NC}"
      return 0
    fi
    sleep 2
    elapsed=$((elapsed + 2))
    echo -e "${YELLOW}  ... node${nid} committed_index=${replica:-?}, alvo=${target} (${elapsed}s)${NC}"
  done
  echo -e "${YELLOW}AVISO: timeout (${timeout}s) aguardando sync de node${nid}${NC}" >&2
  return 1
}

show_persist() {
  local n="${1#node}"
  n="${n%%:*}"
  local path="$ROOT/data/node${n}/node${n}.json"
  echo -e "${BOLD}--- data/node${n}/node${n}.json ---${NC}"
  if [[ -f "$path" ]]; then
    cat "$path"
  else
    echo "(arquivo não encontrado: $path)"
  fi
  echo
}

section() {
  echo
  echo -e "${BLUE}${BOLD}============================================================${NC}"
  echo -e "${BLUE}${BOLD}  $1${NC}"
  echo -e "${BLUE}${BOLD}============================================================${NC}"
  echo
}

step_note() {
  echo -e "${GREEN}- $1${NC}"
}

# Rótulo explícito e bem destacado do subcenário sendo testado no fluxo do driver
# (ex.: "1.1 - Inicialização dos 4 nós"). Aparece só nesta janela (do script de teste).
sub() {
  local text="  >> SUBCENÁRIO $1"
  local line
  line="$(printf '=%.0s' $(seq 1 60))"
  echo
  echo -e "${YELLOW}${BOLD}${line}${NC}"
  echo -e "${YELLOW}${BOLD}${text}${NC}"
  echo -e "${YELLOW}${BOLD}${line}${NC}"
}

# --- Cenário 1 - Operação Normal ---
scenario_1() {
  section "Cenário 1 - Operação Normal"

  sub "1.1 - Inicialização dos quatro nós"
  step_note "Os 4 nós já foram iniciados pelo run-scenarios.sh (docker compose up)."
  step_note "Conferindo o status dos containers:"
  pause_key
  dc ps

  sub "1.2 - Eleição automática de líder"
  step_note "Observe na janela de logs quem é eleito LIDER (~10s)."
  pause_key "Pressione uma tecla quando o líder estiver visível nos logs... "

  sub "1.3 - Publicação de dados pelo cliente"
  step_note "Publicar cidade=curitiba"
  pause_key
  run_client publish cidade curitiba
  step_note "Publicar estado=parana"
  pause_key
  run_client publish estado parana

  sub "1.4 - Replicação das operações"
  step_note "Cada publish acima só retornou OK após commit por quórum (3/4)."
  step_note "Veja nos logs: 'OK replicado ate index=' (seguidores) e 'APLICADO (committed)'."
  pause_key
  dc logs --tail 30 node1 node2 node3 node4 2>/dev/null \
    | grep -iE "replicado|APLICADO" | tail -n 12 || true

  sub "1.5 - Consumo dos dados armazenados"
  step_note "Consumir todos os pares committed"
  pause_key
  run_client consume
  step_note "Consumir chave 'cidade'"
  pause_key
  run_client consume cidade
}

# --- Cenário 2 - Falha do Líder ---
scenario_2() {
  section "Cenário 2 - Falha do Líder"

  sub "2.1 - Interrupção do líder atual"
  step_note "Veja qual nó é o líder na janela de logs."
  local leader=""
  while [[ ! "$leader" =~ ^[1-4]$ ]]; do
    read -r -p "Digite o número do nó líder para parar (1-4): " leader
  done
  step_note "Parar node${leader}"
  pause_key
  dc stop "node${leader}"

  sub "2.2 - Eleição de novo líder"
  step_note "Aguarde nova eleição nos logs (~10s)"
  pause_key "Pressione uma tecla quando o novo líder aparecer... "

  sub "2.3 - Continuidade das operações de publicação e consumo"
  step_note "Publicar pais=brasil (cliente redireciona ao novo líder)"
  pause_key
  run_client publish pais brasil
  step_note "Consumir chave 'pais'"
  pause_key
  run_client consume pais

  # Reintegra o antigo líder ANTES de seguir: o quórum exige 3 de 4 nós.
  step_note "Reintegrar node${leader} (antigo líder) - mantém quórum p/ próximos cenários"
  pause_key
  dc start "node${leader}"
  wait_for_replica_sync "$leader" 0 60 || true
}

# --- Cenário 3 - Persistência (subpassos 4/5/6 do enunciado = 3.1/3.2/3.3) ---
scenario_3() {
  section "Cenário 3 - Persistência"

  sub "3.1 - Encerramento de um nó"
  step_note "Estado persistido de node3 ANTES de parar (para comparar depois)"
  pause_key
  show_persist node3
  step_note "Parar node3 (shutdown limpo grava termo/voto/log/commit em disco)"
  pause_key
  dc stop node3

  sub "3.2 - Reinicialização do processo"
  step_note "Reiniciar node3"
  pause_key
  dc start node3

  sub "3.3 - Recuperação automática do estado persistido"
  step_note "Logs recentes do node3 (recupera do disco e volta como Seguidor)"
  pause_key
  dc logs node3 2>/dev/null | tail -n 20 || true
  step_note "Estado persistido em disco após reinício (data/node3/node3.json)"
  pause_key
  show_persist node3
}

# --- Cenário 4 - Recuperação de Réplica ---
scenario_4() {
  section "Cenário 4 - Recuperação de Réplica (sync incremental)"

  sub "4.1 - Interrupção de uma réplica"
  step_note "Detectando o líder para escolher uma réplica (não o líder)..."
  local leader rep
  leader=$(find_leader_id || true)
  rep=$(pick_replica_id "${leader:-0}")
  step_note "Líder atual: node${leader:-?}; parar réplica node${rep}"
  pause_key
  dc stop "node${rep}"

  sub "4.2 - Execução de novas operações (com a réplica fora)"
  local target_index=0 idx
  step_note "Publicar a=1, b=2, c=3"
  pause_key
  idx=$(publish_and_get_index a 1) && [[ -n "$idx" ]] && target_index="$idx"
  pause_key
  idx=$(publish_and_get_index b 2) && [[ -n "$idx" ]] && target_index="$idx"
  pause_key
  idx=$(publish_and_get_index c 3) && [[ -n "$idx" ]] && target_index="$idx"

  sub "4.3 - Reinicialização da réplica"
  step_note "Estado persistido de node${rep} ANTES de reintegrar (defasado do líder)"
  pause_key
  show_persist "node${rep}"
  step_note "Reiniciar node${rep}"
  pause_key
  dc start "node${rep}"

  sub "4.4 - Sincronização automática apenas das entradas ausentes"
  step_note "Nos logs de node${rep}: AppendEntries reenviam SÓ o trecho ausente (não a base toda)."
  pause_key
  dc logs "node${rep}" 2>/dev/null | grep -iE "replicado|APLICADO" | tail -n 12 || true
  step_note "Aguardar node${rep} alcançar o índice do líder (poll automático)"
  pause_key
  wait_for_replica_sync "$rep" "$target_index" 90 || true
  step_note "Consumir via node${rep} (réplica recuperada)"
  pause_key
  run_client consume --node "node${rep}:600${rep}"
}

# --- Cenário 5 - Consistência de Leitura ---
scenario_5() {
  section "Cenário 5 - Consistência de Leitura"

  sub "5.1 - Leitura tanto no líder quanto nas réplicas"
  step_note "Lendo os 4 nós - o cliente marca cada resposta como [lider] ou [replica]."
  local n
  for n in 1 2 3 4; do
    step_note "Leitura em node${n}"
    pause_key
    run_client consume --node "node${n}:600${n}"
  done

  sub "5.2 - Apenas dados efetivados (committed) são retornados"
  step_note "Nas saídas acima, compare os campos por nó:"
  step_note "  - 'items' lista SOMENTE entradas committed;"
  step_note "  - 'committed_index' = até onde está efetivado;"
  step_note "  - 'pending(uncommitted)' fica de FORA dos items (não é retornado ao cliente)."
  pause_key
}

free_mode_help() {
  cat <<'EOF'
Modo livre - comandos:
  publish <chave> <valor>
  consume [chave] [--node nodeX:600X]
  stop <nodeN>              ex: stop node2
  start <nodeN>             ex: start node3
  logs <nodeN>              tail dos logs do nó
  cat <nodeN>               mostra nodeN.json persistido
  help                      esta ajuda
  quit                      sair (cluster continua rodando)
EOF
}

run_free_command() {
  local line="$1"
  # shellcheck disable=SC2206
  local parts=($line)
  [[ ${#parts[@]} -eq 0 ]] && return 0

  case "${parts[0]}" in
    publish)
      if [[ ${#parts[@]} -ne 3 ]]; then
        echo "uso: publish <chave> <valor>"
        return 1
      fi
      run_client publish "${parts[1]}" "${parts[2]}"
      ;;
    consume)
      run_client consume "${parts[@]:1}"
      ;;
    stop)
      [[ ${#parts[@]} -eq 2 ]] || { echo "uso: stop nodeN"; return 1; }
      dc stop "${parts[1]}"
      ;;
    start)
      [[ ${#parts[@]} -eq 2 ]] || { echo "uso: start nodeN"; return 1; }
      dc start "${parts[1]}"
      ;;
    logs)
      [[ ${#parts[@]} -eq 2 ]] || { echo "uso: logs nodeN"; return 1; }
      dc logs "${parts[1]}" 2>/dev/null | tail -n 30 || true
      ;;
    cat)
      [[ ${#parts[@]} -eq 2 ]] || { echo "uso: cat nodeN"; return 1; }
      show_persist "${parts[1]}"
      ;;
    help)
      free_mode_help
      ;;
    quit|exit|q)
      echo "Encerrando driver. Use 'docker compose down' na pasta do projeto para parar o cluster."
      exit 0
      ;;
    *)
      echo "Comando desconhecido: ${parts[0]} (digite help)"
      return 1
      ;;
  esac
}

free_mode() {
  section "Modo livre - comandos customizados"
  free_mode_help
  echo -e "${GREEN}Cenários 1–5 concluídos. Digite comandos abaixo (help para ajuda, quit para sair).${NC}"
  echo
  while true; do
    if ! IFS= read -r -p "> " line; then
      echo
      echo "Entrada encerrada. Digite quit para sair ou continue com comandos."
      continue
    fi
    [[ -z "${line//[[:space:]]/}" ]] && continue
    run_free_command "$line" || true
  done
}

run_scenario() {
  local name="$1"
  shift
  if ! "$@"; then
    echo -e "${YELLOW}AVISO: ${name} terminou com erros - continuando...${NC}" >&2
  fi
}

main() {
  echo -e "${BOLD}Av5 - demonstração interativa (cliente)${NC}"
  echo "Diretório: $ROOT"
  echo "Use a outra janela para acompanhar os logs dos nós."
  echo

  run_scenario "Cenário 1" scenario_1
  run_scenario "Cenário 2" scenario_2
  run_scenario "Cenário 3" scenario_3
  run_scenario "Cenário 4" scenario_4
  run_scenario "Cenário 5" scenario_5

  free_mode
}

main "$@"
