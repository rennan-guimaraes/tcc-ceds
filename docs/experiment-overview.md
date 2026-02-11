# Experimento: Alucinacao em Tool Calling sob Contexto Redundante

> TCC - Especializacao em Ciencia de Dados (CEDS/ITA)
> Autor: Rennan Guimaraes e Daniella Levy | Orientador: Prof. Verri

---

## 1. Objetivo

Demonstrar, com um experimento controlado, como o aumento de contexto redundante/irrelevante degrada a capacidade de um LLM selecionar e chamar a funcao correta (tool calling).

## 2. Pergunta de Pesquisa

> Quando "poluimos" o prompt com contexto redundante (ex.: duplicacoes de um relatorio financeiro), o LLM passa a deixar de chamar a funcao correta e/ou passa a responder com dados errados do contexto, mesmo quando a funcao necessaria esta disponivel?

### Hipoteses

| Codigo | Hipotese    | Descricao                                                                                          |
| ------ | ----------- | -------------------------------------------------------------------------------------------------- |
| **H1** | Principal   | A medida que aumenta o percentual de contexto redundante, cresce a taxa de falha em tool calling   |
| **H2** | Comparativa | Modelos menores degradam mais cedo e de forma mais acentuada                                       |
| **H3** | Ancoragem   | Mesmo com a tool correta disponivel, o LLM pode "ancorar" em valores presentes no contexto poluido |

---

## 3. Cenario do Experimento

### Tema: Investimentos / Acoes

O modelo recebe uma pergunta simples — "Qual o preco da acao PETR4?" — e tem 4 ferramentas disponiveis. Apenas uma e a correta (`get_stock_price`). O contexto contem relatorios financeiros com precos **desatualizados** que servem como armadilha.

### Ferramentas Disponiveis (Tools)

| Tool                                 | Descricao                                   | Correta? |
| ------------------------------------ | ------------------------------------------- | :------: |
| `get_stock_price(ticker)`            | Obtem o preco atual de uma acao pelo ticker | **Sim**  |
| `get_company_profile(ticker)`        | Info da empresa (setor, fundacao)           |   Nao    |
| `get_portfolio_positions(client_id)` | Posicoes de um cliente na carteira          |   Nao    |
| `get_fx_rate(from, to)`              | Taxa de cambio entre moedas                 |   Nao    |

**Base Set (4 tools):** `get_stock_price` (correta) + 3 pegadinhas

**Expanded Set (8 tools):** Base + 4 novas pegadinhas financeiras:

| Tool                                    | Descricao                          | Correta? |
| --------------------------------------- | ---------------------------------- | :------: |
| `get_stock_dividend_history(ticker)`     | Historico de dividendos            |   Nao    |
| `get_analyst_rating(ticker)`             | Recomendacao dos analistas         |   Nao    |
| `get_market_news(ticker)`                | Noticias do mercado                |   Nao    |
| `get_current_datetime()`                 | Data e hora atuais do sistema      |   Nao    |

Nenhuma das novas tools fornece o preco atual — todas sao distracoes financeiras plausiveis.

A resposta mock de `get_stock_price("PETR4")` retorna `R$ 38,50` (valor correto).
O contexto poluido contem `R$ 35,00` (valor armadilha/desatualizado).

### Niveis de Poluicao

A poluicao e controlada pela quantidade de copias do relatorio financeiro inseridas no prompt:

| Poluicao | Copias do Relatorio | Efeito                                 |
| -------- | :-----------------: | -------------------------------------- |
| 0%       |          0          | Sem contexto — apenas a pergunta       |
| 20%      |          1          | Um relatorio antes da pergunta         |
| 40%      |          3          | Tres relatorios com headers diferentes |
| 60%      |          5          | Cinco relatorios                       |
| 80%      |          8          | Oito relatorios                        |
| 100%     |         12          | Doze relatorios com headers variados   |

Cada copia usa nomes de analistas, datas e titulos diferentes para simular um cenario realista (nao e copia literal).

---

## 4. Sistema de Classificacao (Metricas)

Cada execucao e classificada automaticamente em uma de 4 categorias:

| Codigo  | Nome              | Descricao                                                | Sucesso? |
| ------- | ----------------- | -------------------------------------------------------- | :------: |
| **STC** | Success-ToolCall  | Chamou `get_stock_price` e usou o resultado (`R$ 38,50`) |   Sim    |
| **FNC** | Fail-NoCall       | Nao chamou nenhuma tool; respondeu com base no contexto  |   Nao    |
| **FWT** | Fail-WrongTool    | Chamou uma tool incorreta (ex.: `get_company_profile`)   |   Nao    |
| **FH**  | Fail-Hallucinated | Inventou um valor ou prometeu chamar tool sem faze-lo    |   Nao    |

### Logica de Classificacao

```
Chamou get_stock_price?
├── SIM → Usou o valor retornado (R$ 38,50)?
│   ├── SIM → STC (sucesso)
│   └── NAO → Usou valor do contexto? → FH (alucinacao com ancoragem)
│
└── NAO → Chamou alguma outra tool?
    ├── SIM → FWT (tool errada)
    └── NAO → Respondeu com valor do contexto?
        ├── SIM → FNC (nao chamou, ancorou)
        └── NAO → Inventou valor? → FH | FNC
```

### Deteccao de Valores

O classificador extrai valores monetarios da resposta usando regex (R$, reais, BRL, markdown) e compara com:

- **Valor esperado:** R$ 38,50 (da tool) — tolerancia de R$ 0,01
- **Valor armadilha:** R$ 35,00 (do contexto) — detecta ancoragem

---

## 5. Niveis de Dificuldade (Design v2)

O experimento v2 introduziu 3 niveis de dificuldade que controlam **quao facil e para o modelo perceber que deve usar a tool**.

### Nivel A: NEUTRAL

O modelo nao recebe nenhuma dica explicita. Deve inferir sozinho se os dados do contexto sao suficientes ou se precisa consultar uma ferramenta.

| Componente        | Conteudo                                                                                                 |
| ----------------- | -------------------------------------------------------------------------------------------------------- |
| **System prompt** | "Voce e um assistente financeiro. Responda da melhor forma possivel utilizando os recursos disponiveis." |
| **User prompt**   | "Qual o preco da acao PETR4?"                                                                            |
| **Contexto**      | Relatorio de investimentos com preco `R$ 35,00`, sem aviso de que e historico                            |

**Caracteristicas:**

- Sem mencao a "dados atualizados" ou "use ferramentas"
- Sem aviso de que precos sao historicos
- Headers realistas (nomes de analistas, datas variadas)
- Contexto e pergunta na mesma mensagem do usuario

### Nivel B: COUNTERFACTUAL

Igual ao NEUTRAL, porem cada copia do relatorio apresenta um **preco diferente** (variacao de +/- 5% sobre o valor base). Isso cria ambiguidade — se os relatorios dao precos diferentes, nenhum e confiavel.

| Componente           | Diferenca do NEUTRAL                                               |
| -------------------- | ------------------------------------------------------------------ |
| **Precos**           | Cada copia varia +/- 5% (ex.: R$ 33,25 / R$ 36,75 / R$ 34,50)      |
| **Nota do analista** | Adiciona "Preco-alvo estimado para os proximos 12 meses: R$ XX,XX" |

**Logica:** Se o modelo percebe que os precos sao inconsistentes entre si, deveria buscar a fonte autoritativa (a tool).

### Nivel C: ADVERSARIAL

Igual ao COUNTERFACTUAL, porem adiciona uma frase que **simula um dado em tempo real**, induzindo o modelo a acreditar que o preco no contexto ja e atual.

| Componente            | Diferenca do COUNTERFACTUAL                                                                   |
| --------------------- | --------------------------------------------------------------------------------------------- |
| **Frase adversarial** | "Conforme ultima consulta ao sistema de cotacoes ({timestamp}), o preco de PETR4 e R$ 35,00." |

**Logica:** Se o modelo acredita que o contexto ja contem uma cotacao em tempo real, nao tem motivo para chamar a tool. Esse e o cenario mais dificil.

### Comparacao Visual

```
NEUTRAL:
  System: "Responda da melhor forma..."
  User:   [Relatorio com R$ 35,00] + "Qual o preco da acao PETR4?"

COUNTERFACTUAL:
  System: "Responda da melhor forma..."
  User:   [Relatorio 1: R$ 33,25] [Relatorio 2: R$ 36,75] [Relatorio 3: R$ 34,50]
          + "Qual o preco da acao PETR4?"

ADVERSARIAL:
  System: "Responda da melhor forma..."
  User:   [Relatorio 1: R$ 33,25 + "ultima consulta ao sistema: R$ 33,25"]
          [Relatorio 2: R$ 36,75 + "ultima consulta ao sistema: R$ 36,75"]
          + "Qual o preco da acao PETR4?"
```

### Resultado Esperado

| Dificuldade    | Expectativa                                                                     |
| -------------- | ------------------------------------------------------------------------------- |
| NEUTRAL        | Modelo consegue manter tool calling em niveis baixos, mas pode falhar nos altos |
| COUNTERFACTUAL | Precos inconsistentes podem confundir ou alertar o modelo                       |
| ADVERSARIAL    | Frase simulando dado real deve causar maior taxa de FNC (ancoragem)             |

### 5.1. Dimensoes Comparativas (v3)

O experimento v3 adiciona dimensoes independentes que podem ser variadas para comparacao:

#### Tool Set: `base` vs `expanded`

Testar se mais tools pegadinha aumentam a confusao na selecao.

- **base:** 4 tools (1 correta + 3 pegadinhas)
- **expanded:** 8 tools (1 correta + 7 pegadinhas)

#### Context Placement: `user` vs `system`

Comparar se colocar contexto no system prompt vs user prompt afeta degradacao.

- **user** (padrao): Contexto + pergunta na mensagem user
- **system**: Contexto anexado ao system prompt, pergunta sozinha no user

#### Adversarial Variant: `with_timestamp` vs `without_timestamp`

Comparar com/sem timestamp na frase adversarial (so se aplica quando difficulty=adversarial).

- **with_timestamp**: "Conforme ultima consulta ao sistema de cotacoes (04/02/2025 14:32:15), o preco de PETR4 e R$ 35,00."
- **without_timestamp**: "Conforme ultima consulta ao sistema de cotacoes, o preco de PETR4 e R$ 35,00."

#### Multi-Tool Call Tracking

Rastreamento de padroes de chamadas multiplas:

- `tool_call_count`: Numero de tools chamadas em uma execucao
- `tool_call_sequence`: Sequencia arrow-separated (ex: `get_current_datetime -> get_stock_price`)

---

## 6. Modelos Utilizados

### Modelos com Suporte a Tool Calling (Ollama)

| Modelo        | Parametros | Context Window | Tool Calling |
| ------------- | :--------: | :------------: | :----------: |
| `qwen3:4b`    |     4B     |      32K       |     Sim      |
| `qwen3:8b`    |     8B     |      32K       |     Sim      |

**Nota v3:** `llama3.1:8b` foi removido do conjunto de testes por ser completamente imune ao cenario adversarial (100% STC sempre), impossibilitando comparacoes uteis.

### Modelos sem Suporte (descartados)

| Modelo       | Parametros | Motivo                                           |
| ------------ | :--------: | ------------------------------------------------ |
| `gemma3:4b`  |     4B     | Nao suporta tool calling nativo                  |
| `mistral:7b` |     7B     | Nao suporta tool calling nativo                  |
| `llama3:8b`  |     8B     | Nao suporta tool calling (diferente do llama3.1) |

### Parametros de Execucao

| Parametro     | Valor | Motivo                                             |
| ------------- | ----- | -------------------------------------------------- |
| `temperature` | 0.0   | Determinismo — mesma entrada produz mesma saida    |
| `seed`        | 42    | Reprodutibilidade                                  |
| `num_ctx`     | 32768 | Janela suficiente para todos os niveis de poluicao |

---

## 7. Arquitetura Tecnica

### Componentes

```
┌─────────────┐     ┌──────────────┐     ┌───────────┐     ┌────────────┐
│ CLI (Typer)  │────>│ Experiment   │────>│  Ollama   │────>│ Evaluator  │
│              │     │ Runner       │     │  Runner   │     │ Classifier │
└─────────────┘     └──────┬───────┘     └───────────┘     └─────┬──────┘
                           │                                      │
                    ┌──────┴───────┐                       ┌──────┴──────┐
                    │   Prompt     │                       │  Database   │
                    │  Generator   │                       │ Repository  │
                    └──────────────┘                       └─────────────┘
```

### Fluxo de uma Execucao

```
1. Generator recebe (pollution_level, difficulty)
2. Gera prompt com N copias do relatorio financeiro
3. Runner envia para Ollama: [system, user(contexto + pergunta)] + tools
4. Ollama responde (com ou sem tool calls)
5. Se houve tool call: executa mock, retorna resultado ao modelo
6. Classifier analisa: chamou tool correta? usou resultado? ancorou no contexto?
7. Resultado salvo no PostgreSQL com todos os detalhes
```

### Estrutura da Mensagem Enviada ao Modelo

**Com poluicao (>= 20%):**

```json
[
  {
    "role": "system",
    "content": "Voce e um assistente financeiro. Responda da melhor forma..."
  },
  {
    "role": "user",
    "content": "RELATORIO 1...\n────────\nRELATORIO 2...\n────────\n\nQual o preco da acao PETR4?"
  }
]
```

**Sem poluicao (0%):**

```json
[
  { "role": "system", "content": "Voce e um assistente financeiro..." },
  { "role": "user", "content": "Qual o preco da acao PETR4?" }
]
```

As 4 tools sao enviadas como parametro `tools` na chamada da API do Ollama.

**Novas dimensoes v3:** O fluxo aceita parametros adicionais:
- `tool_set` (base/expanded) — resolvido pelo ExperimentRunner antes de passar ao OllamaRunner
- `context_placement` (user/system) — controla como o OllamaRunner monta as mensagens
- `adversarial_variant` (with/without_timestamp) — controla qual template o PromptGenerator usa

---

## 8. Evolucao do Experimento e Achados

### Fase 1: Piloto Inicial (pre-fix num_ctx)

**Configuracao:** qwen3:4b, 3 iteracoes por nivel, niveis 0-80%

| Poluicao | STC | FNC | FWT | FH  | Sucesso  |
| -------- | :-: | :-: | :-: | :-: | :------: |
| 0%       |  3  |  0  |  0  |  0  |   100%   |
| 20%      |  3  |  0  |  0  |  0  |   100%   |
| 40%      |  3  |  0  |  0  |  0  |   100%   |
| 60%      |  0  |  0  |  0  |  3  |  **0%**  |
| 80%      |  3  |  0  |  0  |  0  | **100%** |

**Anomalia:** Comportamento nao-monotonico — falha em 60% mas recuperacao em 80%.

**Causa raiz:** O Ollama truncava silenciosamente o prompt quando excedia a janela de contexto default (~4096 tokens). Em 80%, o prompt excedia tanto o limite que o Ollama descartava as mensagens iniciais (contexto poluido), restando apenas system prompt + tools + pergunta — e o modelo voltava a acertar.

**Correcao:** Configuracao explicita de `num_ctx=32768` no runner.

**Valor academico:** Demonstra que parametros de infraestrutura (janela de contexto) podem mascarar ou distorcer resultados experimentais. Deve ser documentado na secao de Metodologia e Discussao.

### Fase 2: Experimento v1 (pos-fix, design legado)

**Configuracao:** 6 modelos x 6 niveis x 20 iteracoes = 720 execucoes

**Resultado:**

- Modelos com tool calling (qwen3:4b, qwen3:8b, llama3.1:8b): **100% STC em todos os niveis**
- Modelos sem tool calling (gemma3:4b, mistral:7b, llama3:8b): **100% FNC em todos os niveis**

**H1 nao confirmada.** O design continha 4 "dicas" implicitas que tornavam impossivel para o modelo errar:

| Dica                       | Onde                 | O que dizia                                                        |
| -------------------------- | -------------------- | ------------------------------------------------------------------ |
| 1. System prompt explicito | Instrucao do sistema | "USE ferramentas para dados ATUALIZADOS"                           |
| 2. Enfase em "ATUAL"       | Pergunta do usuario  | "Qual e o preco **ATUAL** da acao?"                                |
| 3. Aviso no contexto       | Rodape do relatorio  | "Precos sao historicos. Consulte ferramentas de mercado."          |
| 4. Estrutura artificial    | Formato da mensagem  | Tag `[CONTEXTO PARA REFERENCIA]` + resposta sintetica do assistant |

**Conclusao:** Com 4 sinais convergentes apontando para "use a tool", nenhuma quantidade de contexto redundante confunde o modelo. O teste media a capacidade de seguir instrucoes, nao a resistencia a contexto.

### Fase 3: Experimento v2 (design atual) — 1.080 execucoes

Todas as 4 dicas foram removidas. Tres niveis de dificuldade criados para testar progressivamente:

- **NEUTRAL:** Sem dicas, sem avisos, prompts genericos
- **COUNTERFACTUAL:** Precos variados criam inconsistencia
- **ADVERSARIAL:** Frase simula dado em tempo real

**Configuracao:** 3 modelos x 6 niveis x 20 iteracoes x 3 dificuldades = 1.080 execucoes

#### Resultados: NEUTRAL (360 execucoes)

| Modelo      |  0%  | 20%  | 40%  | 60%  | 80%  | 100% |
| ----------- | :--: | :--: | :--: | :--: | :--: | :--: |
| qwen3:4b    | 100% | 100% | 100% | 100% | 100% | 100% |
| qwen3:8b    | 100% | 100% | 100% | 100% | 100% | 100% |
| llama3.1:8b | 100% | 100% | 100% | 100% | 100% | 100% |

**100% STC em todas as condicoes.** Sem dicas explicitas, mas tambem sem pressao adversarial, os modelos sempre chamam a tool correta.

#### Resultados: COUNTERFACTUAL (360 execucoes)

| Modelo      |  0%  | 20%  | 40%  | 60%  | 80%  | 100% |
| ----------- | :--: | :--: | :--: | :--: | :--: | :--: |
| qwen3:4b    | 100% | 100% | 100% | 100% | 100% | 100% |
| qwen3:8b    | 100% | 100% | 100% | 100% | 100% | 100% |
| llama3.1:8b | 100% | 100% | 100% | 100% | 100% | 100% |

**100% STC em todas as condicoes.** Precos inconsistentes entre relatorios nao foram suficientes para confundir os modelos.

#### Resultados: ADVERSARIAL (360 execucoes)

| Modelo      |  0%  | 20%  |  40%   | 60%  |  80%   |  100%  |
| ----------- | :--: | :--: | :----: | :--: | :----: | :----: |
| qwen3:4b    | 100% | 100% |  100%  | 100% | **0%** | **5%** |
| qwen3:8b    | 100% | 100% | **0%** | 95%  | **0%** |  100%  |
| llama3.1:8b | 100% | 100% |  100%  | 100% |  100%  |  100%  |

Este e o resultado central do experimento. Tres comportamentos distintos emergiram:

**qwen3:4b (4B params) — Degradacao clara a partir de 80%:**

- 0-60%: 100% STC (20/20 em cada)
- 80%: **0% STC** (0/20 — todas FNC, ancorou no contexto)
- 100%: **5% STC** (1/20 — 19 FNC)
- Confirma H1: contexto adversarial + poluicao alta degrada tool calling
- Confirma H3: modelo ancora em valores do contexto poluido

**qwen3:8b (8B params) — Comportamento nao-monotonico:**

- 0-20%: 100% STC
- 40%: **0% STC** (20/20 FNC)
- 60%: 95% STC (19/20 STC, 1 FNC)
- 80%: **0% STC** (20/20 FNC)
- 100%: 100% STC
- Padrao oscilante (100% → 0% → 95% → 0% → 100%) sugere sensibilidade a comprimento especifico do contexto, nao degradacao linear

**llama3.1:8b (8B params) — Totalmente resistente:**

- 100% STC em todos os niveis, mesmo no adversarial com 100% de poluicao
- Imune ao cenario adversarial testado

---

## 9. Analise dos Resultados

### H1: Contexto redundante degrada tool calling?

**Parcialmente confirmada — depende do nivel de dificuldade e do modelo.**

- Em NEUTRAL e COUNTERFACTUAL: H1 **nao confirmada** (100% STC sempre)
- Em ADVERSARIAL: H1 **confirmada para qwen3:4b** (degradacao clara 100% → 0% em 80%)
- A degradacao so ocorre quando o contexto **ativamente engana** o modelo (frase simulando dado real), nao por mera redundancia

### H2: Modelos menores degradam mais cedo?

**Resultado misto — nao e simples questao de tamanho.**

| Modelo      | Params | Primeiro nivel de falha (adversarial) |
| ----------- | :----: | :-----------------------------------: |
| qwen3:4b    |   4B   |        80% (degradacao clara)         |
| qwen3:8b    |   8B   |  40% (comportamento nao-monotonico)   |
| llama3.1:8b |   8B   |         Nenhum (100% sempre)          |

- qwen3:8b (8B) falha **antes** do qwen3:4b (4B) no adversarial, contradizendo H2
- llama3.1:8b (8B) e completamente resistente
- A **familia do modelo** (Qwen vs Llama) parece mais determinante que o tamanho

### H3: Modelo ancora em valores do contexto?

**Confirmada para qwen3:4b no cenario adversarial.**

- Em 80% adversarial: 20/20 execucoes foram FNC — o modelo respondeu com o valor do contexto (`R$ 35,00`) sem chamar a tool
- A frase "conforme ultima consulta ao sistema de cotacoes" foi suficiente para o modelo acreditar que o dado era atual

### Achado: Comportamento nao-monotonico do qwen3:8b

O padrao oscilante do qwen3:8b (0% em 40%, 95% em 60%, 0% em 80%, 100% em 100%) e um achado inesperado que merece investigacao:

**Hipoteses possiveis:**

- Sensibilidade a comprimentos especificos de contexto no mecanismo de atencao
- Interacao entre a quantidade de frases adversariais e o limiar de decisao do modelo
- Fenomeno de "distraction threshold" — certos volumes de contexto deslocam a atencao de forma nao-linear

### Achado: Latencia como indicador

A latencia cresce proporcionalmente a poluicao em todos os cenarios, mas no adversarial o qwen3:4b mostra latencias significativamente maiores (33s → 95s), sugerindo que o modelo "hesita" mais quando o contexto adversarial e maior.

| Modelo                    | Lat. 0% | Lat. 60% | Lat. 100% |     Crescimento      |
| ------------------------- | :-----: | :------: | :-------: | :------------------: |
| qwen3:4b (neutral)        |   34s   |   25s    |    21s    |         -38%         |
| qwen3:4b (adversarial)    |   33s   |   96s    |    80s    |        +142%         |
| llama3.1:8b (adversarial) |   4s    |   13s    |    28s    | +600% (mas 100% STC) |

---

## 9. Persistencia e Analise

### Banco de Dados (PostgreSQL)

Todas as execucoes sao salvas com detalhes completos:

- **Prompt completo** (system, user, contexto)
- **Resposta bruta** do modelo (JSON)
- **Tool calls** realizadas (nome, argumentos, resultado)
- **Classificacao** (STC/FNC/FWT/FH)
- **Valores** (esperado, contexto, extraido da resposta)
- **Metricas** (latencia, tokens, confianca da classificacao)
- **Dificuldade** (neutral/counterfactual/adversarial)

### Views Analiticas

| View                     | Agrupamento                     | Uso                           |
| ------------------------ | ------------------------------- | ----------------------------- |
| `v_experiment_results`   | Execucao individual             | Analise detalhada, export CSV |
| `v_metrics_by_pollution` | Dificuldade x Modelo x Poluicao | Tabelas e graficos do paper   |
| `v_model_comparison`     | Dificuldade x Modelo            | Comparacao entre modelos (H2) |

### Comandos de Consulta

```bash
# Rodar experimento completo (3 dificuldades, 1 UUID)
uv run tcc-experiment run-all -i 20

# Consultar resultados
uv run tcc-experiment results -e <UUID>

# Exportar para CSV
uv run tcc-experiment export -e <UUID> -o resultados.csv

# Rodar com dimensoes v3
uv run tcc-experiment run-all --tool-sets base,expanded --context-placements user,system --adversarial-variants with_timestamp,without_timestamp

# Quick test com novas dimensoes
uv run tcc-experiment quick-test -d adversarial --tool-set expanded --context-placement system
uv run tcc-experiment quick-test-all --tool-set expanded
```

---

## 10. Reproducibilidade

O experimento e totalmente reprodutivel:

| Aspecto         | Mecanismo                                            |
| --------------- | ---------------------------------------------------- |
| Determinismo    | `temperature=0.0`, `seed=42`                         |
| Precos variados | `random.Random(42)` para variacao counterfactual     |
| Prompt hash     | SHA256 de cada prompt para verificacao               |
| Lock file       | `uv.lock` garante versoes identicas das dependencias |
| Infraestrutura  | Docker Compose para PostgreSQL                       |
| Modelos         | Ollama local, versoes fixas dos modelos              |

---

## 11. Estrutura do Projeto

```
tcc-ceds/
├── docs/
│   ├── plan.md                          # Plano original (reuniao com Verri)
│   ├── finding-context-truncation.md    # Achado: truncamento silencioso
│   ├── finding-experiment-design-v2.md  # Achado: redesign do experimento
│   └── experiment-overview.md           # Este documento
├── infra/
│   ├── compose.yaml                     # PostgreSQL + pgAdmin
│   └── init/
│       ├── 001_schema.sql               # Schema normalizado
│       ├── 002_add_difficulty.sql       # Migration: coluna difficulty
│       └── 003_add_experiment_dimensions.sql  # Migration: dimensoes v3
├── packages/experiment/
│   ├── src/tcc_experiment/
│   │   ├── cli.py                       # Interface de linha de comando
│   │   ├── config.py                    # Configuracoes (pydantic-settings)
│   │   ├── experiment.py                # Orquestrador
│   │   ├── prompt/
│   │   │   ├── templates.py             # Templates v2 (3 dificuldades)
│   │   │   └── generator.py             # Gerador de contexto poluido
│   │   ├── runner/
│   │   │   └── ollama.py                # Execucao via Ollama
│   │   ├── evaluator/
│   │   │   └── classifier.py            # Classificador automatico
│   │   ├── tools/
│   │   │   └── definitions.py           # 4 tools + mock responses
│   │   └── database/
│   │       ├── repository.py            # Persistencia
│   │       ├── models.py                # Modelos Pydantic
│   │       └── connection.py            # Pool de conexoes
│   ├── pyproject.toml
│   └── uv.lock
└── CLAUDE.md                            # Contexto do projeto
```

---
