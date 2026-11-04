#!/usr/bin/env bash

set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP_COMPOSE=(docker compose -f "$ROOT_DIR/compose.yaml")
TEST_COMPOSE=(docker compose -f "$ROOT_DIR/compose.yaml" -f "$ROOT_DIR/teste/docker-compose.test.yaml")
MONITOR="$ROOT_DIR/docker-monitor.sh"

MONITOR_PID=""
MONITOR_OUTPUT=""
TEST_EXIT_CODE=0

usage() {
  cat <<'EOF'
Uso:
  ./teste/run.sh up                 Sobe a aplicação
  ./teste/run.sh monitor            Executa somente o monitor Docker
  ./teste/run.sh test               Executa somente o teste k6
  ./teste/run.sh run                Sobe, monitora e testa em sequência
  ./teste/run.sh down               Para a aplicação
  ./teste/run.sh status             Mostra o status dos containers

Variáveis úteis:
  APP_MEMORY_LIMIT=1g APP_CPU_LIMIT=2.0
  MONITOR_DURATION=900 MONITOR_INTERVAL=5
  TEST_VUS=10 TEST_RAMP_UP=2m TEST_HOLD=5m TEST_RAMP_DOWN=1m
  TEST_PAGE=all TEST_INTERACTIONS=0

Exemplo completo:
  MONITOR_DURATION=900 TEST_VUS=10 ./teste/run.sh run
EOF
}

start_app() {
  "${APP_COMPOSE[@]}" up -d --build app
}

stop_monitor() {
  if [[ -n "$MONITOR_PID" ]] && kill -0 "$MONITOR_PID" 2>/dev/null; then
    kill -INT "$MONITOR_PID" 2>/dev/null || true
    wait "$MONITOR_PID" 2>/dev/null || true
  fi
  MONITOR_PID=""
}

cleanup_run() {
  local exit_code=$?
  trap - EXIT INT TERM
  stop_monitor
  "${APP_COMPOSE[@]}" down >/dev/null 2>&1 || true
  exit "$exit_code"
}

run_monitor_background() {
  local duration="${MONITOR_DURATION:-900}"
  local interval="${MONITOR_INTERVAL:-5}"
  MONITOR_OUTPUT="$ROOT_DIR/teste/resultados/run-$(date '+%Y%m%d_%H%M%S')"
  mkdir -p "$MONITOR_OUTPUT"
  # The k6 image runs as an unprivileged user and writes its summary here.
  chmod 777 "$MONITOR_OUTPUT"

  bash "$MONITOR" --duration "$duration" --interval "$interval" \
    --output "$MONITOR_OUTPUT" &
  MONITOR_PID=$!
  echo "Monitor iniciado (PID $MONITOR_PID). Saída: $MONITOR_OUTPUT"
}

run_test() {
  export TEST_RESULTS_DIR="/results/$(basename "$MONITOR_OUTPUT")"
  "${TEST_COMPOSE[@]}" run --rm k6
}

write_manifest() {
  local host
  host="$(hostname 2>/dev/null || printf 'unknown')"
  cat > "$MONITOR_OUTPUT/run-manifest.json" <<EOF
{
  "run_directory": "$(basename "$MONITOR_OUTPUT")",
  "host": "$host",
  "base_url": "${TEST_BASE_URL:-http://painel-focos-app:8501}",
  "page": "${TEST_PAGE:-all}",
  "interactions": "${TEST_INTERACTIONS:-0}",
  "configured_vus": "${TEST_VUS:-10}",
  "ramp_up": "${TEST_RAMP_UP:-2m}",
  "hold": "${TEST_HOLD:-5m}",
  "ramp_down": "${TEST_RAMP_DOWN:-1m}",
  "monitor_duration": "${MONITOR_DURATION:-900}",
  "monitor_interval": "${MONITOR_INTERVAL:-5}",
  "app_memory_limit": "${APP_MEMORY_LIMIT:-1g}",
  "app_cpu_limit": "${APP_CPU_LIMIT:-2.0}"
}
EOF
}

write_container_state() {
  docker inspect painel-focos-app --format \
    'OOMKilled={{.State.OOMKilled}} RestartCount={{.RestartCount}} Status={{.State.Status}}' \
    > "$MONITOR_OUTPUT/container-state.txt" 2>/dev/null || true
}

write_report() {
  python3 "$ROOT_DIR/teste/report.py" "$MONITOR_OUTPUT" > "$MONITOR_OUTPUT/resource-report.txt"
}

command="${1:-help}"

case "$command" in
  up)
    start_app
    ;;
  monitor)
    shift
    bash "$MONITOR" "$@"
    ;;
  test)
    run_test
    ;;
  run)
    trap cleanup_run EXIT INT TERM
    start_app
    run_monitor_background
    write_manifest
    set +e
    run_test
    TEST_EXIT_CODE=$?
    set -e
    stop_monitor
    write_container_state
    write_report
    exit "$TEST_EXIT_CODE"
    ;;
  down)
    "${APP_COMPOSE[@]}" down
    ;;
  status)
    "${APP_COMPOSE[@]}" ps
    ;;
  help|-h|--help)
    usage
    ;;
  *)
    echo "Comando desconhecido: $command" >&2
    usage >&2
    exit 1
    ;;
esac
