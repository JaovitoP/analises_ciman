# Relatório de Carga e Estresse

## 1. Resumo

Os testes demonstraram que a aplicação funciona com poucos usuários, mas o
custo por sessão é alto e cresce rapidamente quando os usuários repetem o
carregamento das páginas.

O resultado mais importante foi obtido com 3 usuários virtuais simultâneos,
distribuídos pelas páginas da aplicação:

- 142 iterações em aproximadamente 6 minutos.
- 2,75 GB de memória máxima observada.
- 1,90 GB de memória média observada.
- CPU média de 118,24% e pico de 200,74%.
- FCP p95 de 5,84 segundos.
- Nenhuma falha HTTP ou check funcional.
- Nenhum reinício nesse teste específico.

Em um teste anterior, com limite de memória de aproximadamente 2 GB, a
aplicação chegou ao limite, apresentou um reinício e registrou um evento de
reset de memória. Portanto, os checks funcionais passarem não significa que a
aplicação esteja dimensionada para produção.

## 2. Metodologia

Foi utilizado o k6 com o módulo de navegador Chromium. Essa escolha representa
melhor o comportamento do Streamlit do que um teste HTTP simples, pois cada
usuário mantém uma sessão e a aplicação executa reruns por meio do fluxo do
Streamlit.

O monitoramento foi feito com `docker-monitor.sh`, coletando:

- CPU média e máxima.
- Memória média e máxima.
- Percentual de memória do limite do container.
- Número máximo de PIDs.
- Tráfego de rede.
- Leitura e escrita em bloco.
- Resumo por container.

As métricas do k6 foram persistidas em `k6-summary.json`. O relatório
consolidado da aplicação foi gerado em `resource-report.csv` e
`resource-report.json`.

### Cenário principal

| Parâmetro | Valor |
| --- | ---: |
| Usuários virtuais máximos | 3 |
| Ramp-up | 30 segundos |
| Sustentação | 5 minutos |
| Ramp-down | 30 segundos |
| Página | Todas as páginas, distribuídas entre os usuários |
| Interações de filtro | Desativadas |
| Monitoramento | A cada 5 segundos |

## 3. O Que É Uma Iteração

Uma iteração é uma execução completa do usuário virtual no script do k6. No
cenário atual, ela faz o seguinte:

1. Abre uma nova página Chromium.
2. Acessa a aplicação.
3. Aguarda o carregamento do relatório.
4. Opcionalmente altera um filtro.
5. Fecha a página.

Com `TEST_INTERACTIONS=0`, a iteração não altera filtros, mas a abertura da
página já dispara o processamento completo do Streamlit.

Uma iteração não representa necessariamente uma pessoa diferente. Os mesmos 3
usuários virtuais podem executar várias iterações durante o período de
sustentação. No cenário principal:

- Foram executadas 142 iterações.
- Houve aproximadamente 47 iterações por usuário.
- A duração média foi de 6,88 segundos.
- O p95 da duração foi de 10,47 segundos.
- O FCP médio foi de 2,95 segundos.
- O FCP p95 foi de 5,84 segundos.

Isso significa que o teste mediu 3 sessões concorrentes executando repetidos
carregamentos completos, e não apenas 3 acessos isolados.

## 4. Resultados

### 4.1 Execução principal com 3 usuários

Fonte: `teste/resultados/run-20261104_140713/`.

| Métrica | Resultado |
| --- | ---: |
| Usuários configurados | 3 |
| Usuários máximos observados | 3 |
| Iterações | 142 |
| Checks aprovados | 100% |
| Falhas HTTP | 0% |
| CPU média da aplicação | 118,24% |
| CPU máxima da aplicação | 200,74% |
| Memória média da aplicação | 1,90 GB |
| Memória máxima da aplicação | 2,75 GB |
| PIDs máximos | 87 |
| FCP p95 | 5,84 s |
| Reinícios | 0 |
| Eventos de reset de memória | 0 |

O gerador de carga também consumiu recursos relevantes:

- CPU média: 239,33%.
- CPU máxima: 456,54%.
- Memória máxima: aproximadamente 878 MB.
- PIDs máximos: 893.


### 4.2 Consumo por iteração

No cenário principal, a aplicação transmitiu aproximadamente 756 MB. Dividido
pelas 142 iterações, isso representa cerca de:

```text
5,3 MB transmitidos por iteração
```

Esse valor inclui tabelas, gráficos e demais dados enviados pelo Streamlit.
CPU e memória não podem ser atribuídas exatamente a uma iteração individual,
porque são compartilhadas entre as sessões e permanecem alocadas no processo
do Streamlit.

## 5. Causas Prováveis Do Consumo

O custo elevado é compatível com o comportamento atual do código:

- Cada interação ou abertura de página pode reexecutar o script inteiro.
- A página de estados calcula os 27 estados mesmo sem seleção de estados.
- A página de biomas calcula os 6 biomas mesmo sem seleção de biomas.
- A página de regiões calcula as 8 regiões mesmo sem seleção de regiões.
- Cada cálculo usa cópias, agrupamentos e transformações Pandas.
- Gráficos Matplotlib são gerados a cada processamento.
- As figuras Matplotlib não são fechadas explicitamente.
- O cache atual cobre a leitura dos CSVs, mas não todos os cálculos e gráficos.
- Sessões do Streamlit e objetos de cache podem permanecer em memória.
- O cenário executa muitas iterações por usuário durante a sustentação.

## 6. Recomendações

### Prioridade alta

1. Corrigir o cálculo para processar somente os itens selecionados. Evitar loops
   sobre todos os estados, biomas e regiões quando a tabela ou gráfico não foi
   solicitado.
2. Fechar todas as figuras Matplotlib após enviá-las ao Streamlit, usando
   `plt.close(fig)` ou a estratégia equivalente. Isso é importante porque cada
   rerun pode criar novas figuras, e mantê-las abertas conserva objetos Python,
   buffers de imagem e estruturas internas do Matplotlib em memória. Em carga
   contínua, esse acúmulo pode elevar progressivamente o consumo de RAM e levar
   o container a reiniciar por falta de memória.
3. Aplicar cache aos resultados dos cálculos, não somente à leitura dos CSVs.
   O cache deve considerar dataset, período e filtros como chaves.
4. Pré-calcular estatísticas e séries anuais durante a atualização dos dados,
   reduzindo o trabalho feito durante cada sessão.


## 7. Recomendação Para Produção

### Recomendação atual: não colocar em produção como está

A aplicação não deve ser considerada pronta para produção com base nos
resultados atuais, pelos seguintes motivos:

- Apenas 3 usuários simultâneos consumiram até 2,75 GB de memória.
- Com limite de aproximadamente 2 GB, ocorreu reinício da aplicação.
- O carregamento p95 ficou entre 4,75 e 5,84 segundos.
- A aplicação pode gerar grande quantidade de dados e gráficos por sessão.
- O custo por sessão ainda não possui limite operacional conhecido.
- A instrumentação de limites apresentou divergência entre manifesto e limite
  real.

Isso não significa que a aplicação não possa entrar em produção. Significa que
ela precisa de otimização e de uma nova rodada de validação antes da aprovação.

Com base nesses resultados, a aplicação pode ser usada em ambiente controlado,
homologação ou demonstração, mas não é recomendável publicá-la para acesso
aberto ou carga imprevisível.

