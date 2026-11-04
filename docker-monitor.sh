#!/usr/bin/env bash
#
# docker-monitor.sh
#
# Monitora containers Docker usando somente:
#   docker stats --no-stream
#
# Não requer sudo e não instala pacotes.
# Depende apenas de ferramentas básicas normalmente presentes no Linux:
#   bash, awk, date, sleep, mkdir
#
# Modos de uso:
#   ./docker-monitor.sh
#   ./docker-monitor.sh 3600 10
#   ./docker-monitor.sh 7200 10 /tmp/coleta-docker
#
# Também aceita opções longas:
#   ./docker-monitor.sh --duration 3600 --interval 10 --output ./coleta
#
# O que ele gera:
#   snapshot-inicial.csv       snapshot atual
#   snapshot-inicial_raw.txt   saída bruta do docker stats
#   monitoramento.csv          amostras do período
#   resumo.csv                 resumo por container, em bytes
#   resumo_humano.csv          resumo legível
#   ranking.txt                top 5 por CPU, RAM, Block Write e Net TX
#

set -u
export LC_ALL=C

usage() {
cat <<'EOF'
Uso:
  ./docker-monitor.sh                         # snapshot inicial
  ./docker-monitor.sh 3600 10                 # monitora 1h a cada 10s
  ./docker-monitor.sh 7200 10 /tmp/coleta     # monitora 2h, saída em /tmp/coleta

Opções longas:
  ./docker-monitor.sh --duration 3600 --interval 10 --output ./coleta

Arquivos gerados:
  snapshot-inicial.csv       snapshot atual (valores cumulativos)
  snapshot-inicial_raw.txt   saída bruta do docker stats
  monitoramento.csv          amostras do período (quando duration > 0)
  resumo.csv                 resumo por container em bytes
  resumo_humano.csv          resumo por container em formato legível
  ranking.txt                top 5 por CPU, RAM, Block Write e Net TX
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

HOST="$(hostname -s 2>/dev/null || hostname 2>/dev/null || echo host)"
DEFAULT_OUTPUT="./docker-monitor-${HOST}-$(date '+%Y%m%d_%H%M%S')"

DURATION=0
INTERVAL=10
OUTPUT_DIR=""

# Suporta opções longas e também o formato posicional simples.
if [[ "${1:-}" == --* ]]; then
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --duration)
        [[ $# -ge 2 ]] || { echo "ERRO: --duration requer um valor em segundos."; exit 1; }
        DURATION="$2"
        shift 2
        ;;
      --interval)
        [[ $# -ge 2 ]] || { echo "ERRO: --interval requer um valor em segundos."; exit 1; }
        INTERVAL="$2"
        shift 2
        ;;
      --output)
        [[ $# -ge 2 ]] || { echo "ERRO: --output requer um diretório."; exit 1; }
        OUTPUT_DIR="$2"
        shift 2
        ;;
      --help|-h)
        usage
        exit 0
        ;;
      *)
        echo "ERRO: opção desconhecida: $1"
        usage
        exit 1
        ;;
    esac
  done
else
  DURATION="${1:-0}"
  INTERVAL="${2:-10}"
  OUTPUT_DIR="${3:-$DEFAULT_OUTPUT}"
fi

[[ -z "$OUTPUT_DIR" ]] && OUTPUT_DIR="$DEFAULT_OUTPUT"

if ! [[ "$DURATION" =~ ^[0-9]+$ ]]; then
  echo "ERRO: duração deve ser inteira e em segundos. Ex.: 3600"
  exit 1
fi

if ! [[ "$INTERVAL" =~ ^[0-9]+$ ]]; then
  echo "ERRO: intervalo deve ser inteiro e em segundos. Ex.: 10"
  exit 1
fi

[[ "$INTERVAL" -lt 1 ]] && INTERVAL=1

for cmd in docker awk date sleep mkdir; do
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "ERRO: dependência não encontrada: $cmd"
    exit 1
  fi
done

# Verifica se o usuário atual consegue falar com o Docker.
# Usamos docker stats porque é o comando principal do script.
if ! docker stats --no-stream --format '{{.ID}}' >/dev/null 2>&1; then
  echo "ERRO: não foi possível executar 'docker stats'."
  echo "Verifique se o usuário atual tem acesso ao Docker (grupo docker, socket ou DOCKER_HOST)."
  exit 1
fi

mkdir -p "$OUTPUT_DIR" || {
  echo "ERRO: não foi possível criar o diretório: $OUTPUT_DIR"
  exit 1
}

SNAP="$OUTPUT_DIR/snapshot-inicial.csv"
SNAP_RAW="$OUTPUT_DIR/snapshot-inicial_raw.txt"
MON="$OUTPUT_DIR/monitoramento.csv"
RESUMO="$OUTPUT_DIR/resumo.csv"
RESUMO_H="$OUTPUT_DIR/resumo_humano.csv"
RANK="$OUTPUT_DIR/ranking.txt"

HEADER="timestamp,epoch,container_id,name,cpu_percent,mem_used_bytes,mem_limit_bytes,mem_percent,net_rx_bytes,net_tx_bytes,block_read_bytes,block_write_bytes,pids"

echo "$HEADER" > "$SNAP"
echo "$HEADER" > "$MON"

# Formato tabulado para facilitar o parse.
STATS_FORMAT=$'{{.ID}}\t{{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}\t{{.NetIO}}\t{{.BlockIO}}\t{{.PIDs}}'

collect_sample() {
  local file="$1"
  local ts epoch

  ts="$(date '+%Y-%m-%d %H:%M:%S')"
  epoch="$(date +%s)"

  docker stats --no-stream --format "$STATS_FORMAT" 2>/dev/null | awk -F'\t' -v ts="$ts" -v epoch="$epoch" '
    function trim(s) {
      gsub(/^[ \t\r]+|[ \t\r]+$/, "", s)
      return s
    }

    function tobytes(s,   num, unit, factor) {
      s = trim(s)

      if (s == "" || s == "-" || s == "N/A") return 0

      if (match(s, /^[0-9]+([.][0-9]+)?/) == 0) return 0

      num = substr(s, RSTART, RLENGTH) + 0
      unit = substr(s, RSTART + RLENGTH)
      unit = trim(unit)
      unit = toupper(unit)

      factor = 1

      if (unit == "" || unit == "B") {
        factor = 1
      } else if (unit == "KIB") {
        factor = 1024
      } else if (unit == "MIB") {
        factor = 1024 * 1024
      } else if (unit == "GIB") {
        factor = 1024 * 1024 * 1024
      } else if (unit == "TIB") {
        factor = 1024 * 1024 * 1024 * 1024
      } else if (unit == "K" || unit == "KB") {
        factor = 1000
      } else if (unit == "M" || unit == "MB") {
        factor = 1000 * 1000
      } else if (unit == "G" || unit == "GB") {
        factor = 1000 * 1000 * 1000
      } else if (unit == "T" || unit == "TB") {
        factor = 1000 * 1000 * 1000 * 1000
      } else {
        factor = 1
      }

      return num * factor
    }

    NF >= 7 {
      id = trim($1)
      name = trim($2)
      gsub(/,/, "_", name)

      cpu = trim($3)
      sub(/%/, "", cpu)
      if (cpu !~ /^[0-9]+([.][0-9]+)?$/) cpu = 0

      split($4, mem, "/")
      mem_used = tobytes(mem[1])
      mem_limit = tobytes(mem[2])

      mempct = trim($5)
      sub(/%/, "", mempct)
      if (mempct !~ /^[0-9]+([.][0-9]+)?$/) mempct = 0

      split($6, net, "/")
      net_rx = tobytes(net[1])
      net_tx = tobytes(net[2])

      split($7, blk, "/")
      blk_read = tobytes(blk[1])
      blk_write = tobytes(blk[2])

      pids = trim($8)
      if (pids !~ /^[0-9]+$/) pids = 0

      printf "%s,%s,%s,%s,%.2f,%.0f,%.0f,%.2f,%.0f,%.0f,%.0f,%.0f,%d\n", ts, epoch, id, name, cpu, mem_used, mem_limit, mempct, net_rx, net_tx, blk_read, blk_write, pids
    }
  ' >> "$file"
}

print_top5() {
  local title="$1"
  local sortcol="$2"
  local extracol="$3"
  local header="$4"

  echo "$title"
  echo "$header"

  awk -F',' -v col="$sortcol" -v extra="$extracol" '
    NR == 1 { next }
    {
      v = $col + 0

      out = $1 "," $2 "," $col
      if (extra + 0 > 0) {
        out = out "," $extra
      }

      for (i = 1; i <= 5; i++) {
        if (!(i in val) || v > val[i]) {
          for (j = 5; j > i; j--) {
            val[j] = val[j-1]
            line[j] = line[j-1]
          }

          val[i] = v
          line[i] = out
          break
        }
      }
    }
    END {
      for (i = 1; i <= 5; i++) {
        if (line[i] != "") print line[i]
      }
    }
  ' "$RESUMO"

  echo
}

echo "Docker monitor"
echo "Host:               $HOST"
echo "Diretório de saída: $OUTPUT_DIR"
echo "Duração:            ${DURATION}s"
echo "Intervalo:          ${INTERVAL}s"
echo

if [[ -z "$(docker ps -q 2>/dev/null || true)" ]]; then
  echo "AVISO: nenhum container em execução no momento."
fi

echo "Coletando snapshot inicial..."
docker stats --no-stream > "$SNAP_RAW" 2>/dev/null || true
collect_sample "$SNAP"

if [[ "$DURATION" -eq 0 ]]; then
  echo
  echo "Snapshot concluído."
  echo "Arquivos:"
  echo "  $SNAP"
  echo "  $SNAP_RAW"
  exit 0
fi

echo "Monitorando... Ctrl+C para encerrar."

END_EPOCH=$(( $(date +%s) + DURATION ))
SAMPLES=0
INTERRUPTED=0

trap 'INTERRUPTED=1' INT

while :; do
  NOW_EPOCH="$(date +%s)"

  [[ "$INTERRUPTED" -eq 1 ]] && break
  [[ "$NOW_EPOCH" -ge "$END_EPOCH" ]] && break

  LOOP_START="$NOW_EPOCH"

  collect_sample "$MON"
  SAMPLES=$((SAMPLES + 1))

  NOW_EPOCH="$(date +%s)"

  if [[ "$INTERRUPTED" -eq 1 ]]; then
    break
  fi

  ELAPSED=$((NOW_EPOCH - LOOP_START))
  SLEEP_TIME=$((INTERVAL - ELAPSED))

  [[ "$SLEEP_TIME" -lt 0 ]] && SLEEP_TIME=0

  REMAIN=$((END_EPOCH - NOW_EPOCH))
  [[ "$REMAIN" -lt "$SLEEP_TIME" ]] && SLEEP_TIME="$REMAIN"

  [[ "$SLEEP_TIME" -gt 0 ]] && sleep "$SLEEP_TIME"
done

trap - INT

if [[ "$INTERRUPTED" -eq 1 ]]; then
  echo
  echo "Interrompido pelo usuário. Gerando resumo parcial se houver amostras."
fi

echo "Coleta finalizada. Amostras: $SAMPLES"

if [[ -s "$MON" ]] && awk 'NR > 1 { found = 1; exit } END { exit found ? 0 : 1 }' "$MON"; then
  # Resumo por container.
  #
  # Os campos NET RX/TX e BLOCK READ/WRITE do docker stats são cumulativos.
  # Aqui calculamos a diferença entre amostras para saber quanto ocorreu
  # durante o período monitorado.
  #
  # Se o container reiniciar no meio da coleta, o contador pode resetar.
  # O script trata reset somando o valor atual após o reset, mas naturalmente
  # perde o trecho entre a última amostra antes do restart e o restart em si.
  awk -F',' '
    NR == 1 { next }
    {
      id = $3
      name = $4
      epoch = $2 + 0

      cpu = $5 + 0
      mem = $6 + 0
      memlim = $7 + 0
      mempct = $8 + 0

      rx = $9 + 0
      tx = $10 + 0
      br = $11 + 0
      bw = $12 + 0
      pids = $13 + 0

      if (!(id in seen)) {
        seen[id] = 1
        names[id] = name

        samples[id] = 0

        cpu_sum[id] = 0
        cpu_max[id] = 0

        mem_sum[id] = 0
        mem_max[id] = 0
        memlim_max[id] = 0

        mempct_sum[id] = 0
        mempct_max[id] = 0

        rx_delta[id] = 0
        tx_delta[id] = 0
        br_delta[id] = 0
        bw_delta[id] = 0

        pids_max[id] = 0

        prev_rx[id] = rx
        prev_tx[id] = tx
        prev_br[id] = br
        prev_bw[id] = bw

        last_epoch[id] = epoch
      }

      samples[id]++

      cpu_sum[id] += cpu
      if (cpu > cpu_max[id]) cpu_max[id] = cpu

      mem_sum[id] += mem
      if (mem > mem_max[id]) mem_max[id] = mem
      if (memlim > memlim_max[id]) memlim_max[id] = memlim

      mempct_sum[id] += mempct
      if (mempct > mempct_max[id]) mempct_max[id] = mempct

      if (pids > pids_max[id]) pids_max[id] = pids

      if (epoch >= last_epoch[id]) {
        if (rx >= prev_rx[id]) rx_delta[id] += rx - prev_rx[id]; else rx_delta[id] += rx
        if (tx >= prev_tx[id]) tx_delta[id] += tx - prev_tx[id]; else tx_delta[id] += tx
        if (br >= prev_br[id]) br_delta[id] += br - prev_br[id]; else br_delta[id] += br
        if (bw >= prev_bw[id]) bw_delta[id] += bw - prev_bw[id]; else bw_delta[id] += bw

        prev_rx[id] = rx
        prev_tx[id] = tx
        prev_br[id] = br
        prev_bw[id] = bw

        last_epoch[id] = epoch
      }
    }
    END {
      print "container,name,samples,cpu_avg_pct,cpu_max_pct,mem_avg_bytes,mem_max_bytes,mem_limit_max_bytes,mem_pct_avg,mem_pct_max,net_rx_delta_bytes,net_tx_delta_bytes,block_read_delta_bytes,block_write_delta_bytes,pids_max"

      for (id in seen) {
        if (samples[id] == 0) continue

        printf "%s,%s,%d,%.2f,%.2f,%.0f,%.0f,%.0f,%.2f,%.2f,%.0f,%.0f,%.0f,%.0f,%d\n", id, names[id], samples[id], cpu_sum[id] / samples[id], cpu_max[id], mem_sum[id] / samples[id], mem_max[id], memlim_max[id], mempct_sum[id] / samples[id], mempct_max[id], rx_delta[id], tx_delta[id], br_delta[id], bw_delta[id], pids_max[id]
      }
    }
  ' "$MON" > "$RESUMO"

  # Versão legível do resumo.
  awk -F',' '
    function human(b,   n) {
      b += 0

      if (b >= 1000000000000) {
        n = b / 1000000000000
        return sprintf("%.2fTB", n)
      }

      if (b >= 1000000000) {
        n = b / 1000000000
        return sprintf("%.2fGB", n)
      }

      if (b >= 1000000) {
        n = b / 1000000
        return sprintf("%.2fMB", n)
      }

      if (b >= 1000) {
        n = b / 1000
        return sprintf("%.2fkB", n)
      }

      return sprintf("%.0fB", b)
    }

    NR == 1 {
      print "container,name,samples,cpu_avg_pct,cpu_max_pct,mem_avg,mem_max,mem_limit_max,mem_pct_avg,mem_pct_max,net_rx_delta,net_tx_delta,block_read_delta,block_write_delta,pids_max"
      next
    }

    {
      limit = ($8 + 0 == 0) ? "unlimited" : human($8)

      printf "%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n", $1, $2, $3, $4, $5, human($6), human($7), limit, $9, $10, human($11), human($12), human($13), human($14), $15
    }
  ' "$RESUMO" > "$RESUMO_H"

  # Ranking simples, sem depender de sort/head/tail.
  {
    echo "Gerado em: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "Arquivo base: $RESUMO"
    echo
    echo "As linhas abaixo usam as mesmas colunas do resumo.csv."
    echo

    print_top5 "Top 5 por CPU média (%):" 4 5 "container,name,cpu_avg_pct,cpu_max_pct"
    print_top5 "Top 5 por RAM média (bytes):" 6 7 "container,name,mem_avg_bytes,mem_max_bytes"
    print_top5 "Top 5 por Block Write delta (bytes):" 14 13 "container,name,block_write_delta_bytes,block_read_delta_bytes"
    print_top5 "Top 5 por Net TX delta (bytes):" 12 11 "container,name,net_tx_delta_bytes,net_rx_delta_bytes"
  } > "$RANK"

  echo
  echo "Resumo gerado:"
  echo "  $RESUMO"
  echo "  $RESUMO_H"
  echo "  $RANK"
else
  echo
  echo "Sem amostras suficientes para gerar resumo."
fi

echo
echo "Arquivos gerados em: $OUTPUT_DIR"

exit 0