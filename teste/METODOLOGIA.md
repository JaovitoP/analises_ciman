# Metodologia de Medição

## Unidade de carga

`TEST_VUS` é o número máximo de usuários virtuais simultâneos. Cada usuário
mantém uma sessão de navegador e pode executar mais de uma iteração durante o
tempo de sustentação. Portanto, `VUs` não é o total de visitas realizadas.

O valor observado deve ser conferido em `k6_vus_max` no relatório. O valor
configurado fica em `users_configured`.

## Unidade de recurso

Os recursos da aplicação são lidos exclusivamente das linhas do container
`painel-focos-app` no `monitoramento.csv`. O container k6 é reportado
separadamente porque Chromium pode consumir mais CPU, RAM e PIDs que a própria
aplicação.

O relatório calcula:

- CPU média e máxima.
- Memória média, máxima e percentual máximo do limite.
- Máximo de PIDs.
- Quedas abruptas de memória compatíveis com reinício.
- Iterações, checks, falhas HTTP e FCP p95 do k6.

## Procedimento comparável

Cada nível deve ser executado em uma execução nova, com a mesma página, os
mesmos tempos e um cooldown posterior. Uma matriz recomendada é:

```bash
for users in 1 2 5 10; do
  TEST_VUS="$users" \
  TEST_RAMP_UP=30s TEST_HOLD=5m TEST_RAMP_DOWN=30s \
  MONITOR_DURATION=600 MONITOR_INTERVAL=5 \
  ./teste/run.sh run
done
```

O resultado é considerado inválido ou interrompido quando ocorrer qualquer um
destes eventos:

- `OOMKilled=true`.
- `RestartCount` aumentar.
- `app_memory_reset_events` for maior que zero.
- `k6_checks_rate` ficar abaixo de 0,95.
- Memória da aplicação permanecer acima de 80% do limite.

## Limitações

Se k6 e aplicação compartilharem o mesmo host físico, o gerador de carga pode
competir por CPU e RAM. Para capacidade de produção, execute o k6 em outra
máquina e configure `TEST_BASE_URL` com o endereço acessível da aplicação.

O container Docker da aplicação possui limite configurável. Um aumento de
limite pode evitar um restart, mas não deve ser usado para mascarar crescimento
de memória: primeiro compare memória residual, reinícios e latência entre os
níveis de carga.
