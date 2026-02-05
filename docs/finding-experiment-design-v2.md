# Finding: Redesign do Experimento (v2) - Niveis de Dificuldade

**Data:** 2025-02-04
**Autor:** Rennan Guimaraes

## Problema

O experimento original rodou 720 execucoes (6 modelos x 6 niveis de poluicao x 20 iteracoes). Resultado: modelos com suporte a tool calling (qwen3:4b, qwen3:8b, llama3.1:8b) acertaram **100% em todos os niveis de poluicao**. H1 nao foi confirmada.

### Modelos testados

| Modelo | Tool Calling | Resultado |
|--------|-------------|-----------|
| qwen3:4b | Sim | 100% STC em todos os niveis |
| qwen3:8b | Sim | 100% STC em todos os niveis |
| llama3.1:8b | Sim | 100% STC em todos os niveis |
| gemma3:4b | Nao suportado | 100% FNC (nunca chamou tools) |
| mistral:7b | Nao suportado | 100% FNC (nunca chamou tools) |
| llama3:8b | Nao suportado | 100% FNC (nunca chamou tools) |

### Notas sobre modelos

- `gemma3`, `mistral` e `llama3` nao suportam tool calling no Ollama
- `llama3.1:8b` suporta (diferente do `llama3:8b`)
- Apenas modelos com suporte nativo sao validos para o experimento

## Diagnostico

Analise do design experimental revelou 4 "dicas" que facilitavam demais para o modelo:

1. **System prompt explicito:** "USE ferramentas para dados ATUALIZADOS"
2. **User prompt com enfase:** "preco ATUAL" (enfase em ATUAL)
3. **Aviso no contexto:** Bloco dizendo que precos sao historicos e que se deve usar ferramentas
4. **Estrutura artificial:** Tag `[CONTEXTO PARA REFERENCIA]` + resposta sintetica do assistant ("Entendido. Analisei o contexto...")

Com tantas dicas, o modelo nunca teve "duvida" sobre o que fazer: sempre chamava a tool correta, independente da quantidade de contexto poluido.

## Solucao: 3 Niveis de Dificuldade

### Level A - NEUTRAL

- System prompt neutro: "Voce e um assistente financeiro. Responda da melhor forma possivel utilizando os recursos disponiveis."
- User prompt sem enfase: "Qual o preco da acao {ticker}?"
- Contexto sem aviso sobre dados historicos
- Copias com headers realistas (nomes de analistas, datas diferentes)
- Contexto e pergunta na mesma mensagem (sem tag artificial)

### Level B - COUNTERFACTUAL

- Mesmo system/user do NEUTRAL
- Cada copia do contexto com preco ligeiramente diferente (+/- 5% do base)
- Datas, analistas e headers diferentes por copia
- Nota de analista com preco-alvo estimado

### Level C - ADVERSARIAL

- Mesmo que COUNTERFACTUAL
- Frase que simula dado em tempo real: "Conforme ultima consulta ao sistema de cotacoes ({timestamp}), o preco de {ticker} e {context_price}"

## Mudancas tecnicas

### Templates (`templates.py`)
- Enum `DifficultyLevel` com valores: `neutral`, `counterfactual`, `adversarial`
- 3 novos templates (v2) sem as dicas do legado
- Template legado preservado como `stock_price_query` para reprodutibilidade

### Generator (`generator.py`)
- Aceita parametro `difficulty` no construtor
- Headers realistas rotacionados entre copias (lista de 12 analistas/datas)
- Precos counterfactual gerados com `random.Random(42)` para reprodutibilidade
- Campo `difficulty_level` no `GeneratedPrompt`

### Runner (`ollama.py`)
- Contexto e pergunta na mesma mensagem do usuario
- Removida tag `[CONTEXTO PARA REFERENCIA]`
- Removida resposta sintetica do assistant

### CLI (`cli.py`)
- Opcao `--difficulty / -d` nos comandos `run` e `quick-test`

## Valor academico

Este achado e relevante para o paper:

- **Metodologia:** Demonstra a importancia do design experimental em avaliacoes de LLMs
- **Discussao:** Muitos benchmarks podem ter o mesmo problema (dicas implicitas que inflam resultados)
- **Contribuicao:** Framework de 3 niveis permite avaliar a robustez real do modelo

## Proximos passos

1. Rodar experimento com os 3 niveis de dificuldade
2. Comparar resultados entre niveis (espera-se degradacao progressiva)
3. Se NEUTRAL ja degradar, o achado e forte
4. Se so ADVERSARIAL degradar, mostra que o modelo precisa de "incentivo forte" para falhar
