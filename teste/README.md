# Teste de carga e estresse

Este diretório contém os testes de carga da aplicação Streamlit usando o k6
com Chromium. O navegador é necessário porque o Streamlit mantém uma sessão
WebSocket e executa reruns do script; um teste HTTP simples mediria somente o
carregamento inicial.

## Pré-requisitos

- Docker e Docker Compose.
- Recursos suficientes para executar a aplicação e os navegadores do k6.
- O teste deve ser executado contra um ambiente isolado.

## Subir a aplicação

Na raiz do projeto:

```bash
docker compose up -d --build
docker compose ps
```

A aplicação ficará disponível em `http://localhost:8501`.

## Executar tudo com um comando

O script `run.sh` sobe a aplicação, inicia o monitor, executa o k6 e encerra
os containers ao final:

```bash
chmod +x teste/run.sh
MONITOR_DURATION=900 TEST_VUS=10 ./teste/run.sh run
```

Os resultados do monitor são gravados em um diretório com timestamp dentro de
`teste/resultados/`. Para executar etapas isoladas:

```bash
./teste/run.sh up
./teste/run.sh status
./teste/run.sh test
./teste/run.sh down
```

O comando `monitor` também repassa seus argumentos diretamente ao
`docker-monitor.sh`.

Cada execução integrada gera, além dos arquivos do monitor:

- `run-manifest.json`: parâmetros efetivamente usados no teste.
- `k6-summary.json`: métricas persistidas do k6, incluindo usuários virtuais,
  iterações, checks e tempos de carregamento.
- `resource-report.csv`: relação consolidada entre carga e consumo da aplicação.
- `resource-report.json`: a mesma relação em formato estruturado.
- `container-state.txt`: estado final, contador de reinícios e indicação de
  `OOMKilled` quando disponível.

## Como interpretar os resultados

O número de usuários é `users_configured` e o número observado pelo k6 é
`k6_vus_max`. Eles representam usuários virtuais simultâneos, não o número
total de visitas. O k6 pode executar várias iterações por usuário durante o
período de sustentação.

Use `resource-report.csv` para comparar execuções:

| Campo | Significado |
| --- | --- |
| `users_configured` | Usuários virtuais configurados |
| `app_cpu_avg_pct` / `app_cpu_max_pct` | CPU média e máxima da aplicação |
| `app_memory_avg_bytes` / `app_memory_max_bytes` | RAM média e máxima da aplicação |
| `app_memory_reset_events` | Quedas abruptas compatíveis com reinício/OOM |
| `k6_checks_rate` | Taxa de checks aprovados |
| `k6_http_failed_rate` | Taxa de falhas HTTP do navegador |
| `k6_fcp_p95_ms` | Percentil 95 do primeiro conteúdo renderizado |

O consumo do container k6 não entra nos campos `app_*`. Isso evita confundir o
custo do gerador de carga com o custo da aplicação. Ainda assim, se aplicação
e k6 estiverem no mesmo host, o k6 pode disputar CPU e memória com a aplicação.

Para obter uma relação confiável entre usuários e recursos, execute níveis
separados, sempre com o mesmo tempo e um cooldown:

```bash
for users in 1 2 5 10; do
  TEST_VUS="$users" MONITOR_DURATION=600 ./teste/run.sh run
done
```

Compare os `resource-report.csv` de cada diretório. Um teste deve ser
considerado interrompido quando houver `OOMKilled=true`, aumento de
`app_memory_reset_events`, erro de checks ou memória sustentada acima de 80%.

## Executar o teste

O compose do teste é aplicado junto ao compose principal para que o container
k6 consiga acessar a aplicação pelo nome `painel-focos-app`:

```bash
mkdir -p teste/resultados
docker compose -f compose.yaml -f teste/docker-compose.test.yaml \
  run --rm k6
```

Por padrão, o teste sobe até 10 usuários em 2 minutos, mantém a carga por 5
minutos e reduz para zero em 1 minuto. O resultado resumido é exibido pelo k6.

## Monitorar o consumo

Em outro terminal, antes de iniciar o k6:

```bash
bash ./docker-monitor.sh --duration 480 --interval 5 \
  --output ./teste/resultados/carga-01
```

O diretório gerado contém amostras, resumo por container e ranking de CPU,
memória, escrita em bloco e transmissão de rede. O período do monitor deve
cobrir o ramp-up, a sustentação e o ramp-down.

## Configurar o teste

As variáveis podem ser fornecidas diretamente ao comando:

```bash
TEST_VUS=25 TEST_RAMP_UP=5m TEST_HOLD=10m TEST_RAMP_DOWN=2m \
TEST_PAGE=estados TEST_INTERACTIONS=1 \
docker compose -f compose.yaml -f teste/docker-compose.test.yaml run --rm k6
```

Valores aceitos para `TEST_PAGE`: `all`, `brasil`, `biomas`, `estados` e
`regiões`. Com `all`, os usuários são distribuídos entre as quatro páginas.
`TEST_INTERACTIONS=1` altera um filtro de ano para provocar um rerun adicional.

Para limitar os recursos da aplicação durante um teste:

```bash
APP_MEMORY_LIMIT=768m APP_CPU_LIMIT=1.5 docker compose up -d --build
```

## Ordem recomendada

1. Executar uma linha de base com `TEST_VUS=1`.
2. Repetir com 5 e 10 usuários.
3. Aumentar gradualmente para 25 e 50 usuários.
4. Comparar p95, erros, CPU, memória e PIDs.
5. Interromper o teste se a memória ficar sustentadamente acima de 80%, se o
   container reiniciar ou se o host começar a sofrer pressão de memória.

O container `k6` é medido separadamente do container `app`; ao analisar os
resultados, use a linha `painel-focos-app` para avaliar o consumo da aplicação.

## Limpeza

```bash
docker compose down
```
