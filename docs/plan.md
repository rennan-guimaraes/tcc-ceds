1. Objetivo do trabalho (1 frase)

Desenvolver e demonstrar, com um experimento controlado, como o aumento de contexto redundante/irrelevante degrada a capacidade de um LLM selecionar e chamar a função correta (tool calling), e entregar uma ferramenta/script que reproduza e mensure esse fenômeno.

2. Pergunta de pesquisa e hipótese

Pergunta de pesquisa (direta):
Quando “poluímos” o prompt com contexto redundante (ex.: duplicações de um relatório), o LLM passa a deixar de chamar a função correta e/ou passa a responder com dados errados do contexto, mesmo quando a função é necessária?

Hipóteses (testáveis):

H1 (principal): À medida que aumenta o percentual de contexto redundante, cresce a taxa de falha em tool calling (não chamar / chamar errado / usar valor do texto em vez da ferramenta).
H2: Modelos menores (ou menos capazes) degradam mais cedo e de forma mais acentuada.
H3: Mesmo com a tool correta disponível, o LLM pode “ancorar” em valores presentes no contexto poluído (ex.: preço no relatório) e evitar a consulta via função.

3. Escopo e “regra de ouro” para manter simples (o que o Verri quis dizer)

Regra de ouro do Verri (interpretação prática)

O estresse do teste deve estar na quantidade/qualidade de informação no contexto para decidir a tool — não em criar uma plataforma enorme com mil features.

Escopo mínimo viável (MVP do curso)

Um tema único (ex.: ações).
Poucas tools (2 a 4), todas plausíveis no tema.
Um script reprodutível que:

A plataforma “bonita” pode ser um plus (ou pós-curso). Para o curso, o que garante nota é: texto bem fundamentado + experimento funcionando + resultados claros.

4. Desenho do experimento (simples e convincente)

4.1 Tema e cenário base (o que vocês já alinhavam)

Tema: ações/relatório de investimentos
Tarefa: “Obter o preço atual do ativo X”
Armadilha: o contexto contém um relatório com um preço (potencialmente desatualizado) e é duplicado N vezes.

4.2 Conjunto de tools (para evitar “chamar a única disponível”)

Mantenha tools próximas do contexto, mas com finalidades distintas:

get_stock_price(ticker) → a correta para responder “preço atual”
get_company_profile(ticker) → irrelevante para preço, mas plausível
get_portfolio_positions(client_id) → plausível no tema “investimentos”
(opcional) get_fx_rate(pair) → ainda dentro de finanças

Importante: o prompt deve exigir a tool correta para ser considerado certo.

4.3 Variáveis do experimento (o que vai mudar)

Nível de poluição do contexto: 0%, 20%, 40%, 60% (não precisa mais que isso para mostrar curva)
Tamanho do relatório duplicado: curto vs médio (opcional)
Modelo: pelo menos 2 (um menor e um maior) para contraste

4.4 O que é “sucesso” e “falha” (métricas objetivas)

Para cada execução, classificar:

Success-ToolCall (STC): chamou get_stock_price corretamente e usou o resultado.
Fail-NoCall (FNC): não chamou tool e respondeu com base no texto.
Fail-WrongTool (FWT): chamou tool errada.
Fail-Hallucinated (FH): inventou valor/justificativa sem base.

Métricas:

Taxa de sucesso (STC%) por nível de poluição
Taxa de ancoragem no contexto (responde preço do relatório)
(opcional) tempo/custo por execução

5. Implementação: “script primeiro” (MVP técnico)

Componentes mínimos

Gerador de prompt
Runner de modelos
Evaluator
Relatório de resultados

Por que isso é “o fácil” que o Verri citou?

Porque você reduz o problema a:

poucas tools
poucas condições
métrica binária e rastreável
experimento reprodutível

Isso produz evidência rápida e comunicável em 15 páginas.

6. Estrutura sugerida do paper (≈ 15 páginas)

Introdução (1–1,5 p.)
Fundamentação / Trabalhos relacionados (3–4 p.)
Metodologia proposta (3–4 p.)
Implementação (2–3 p.)
Resultados (2–3 p.)
Discussão e limitações (1–1,5 p.)
Conclusão e próximos passos (0,5–1 p.)

7. Decisões do call (registradas como “ata”)

Trabalho terá parte conceitual + parte prática (≈ 15 páginas).
Foco em tool calling sob degradação por contexto redundante (não RAG como centro).
Experimento: “poluir” prompt com duplicações (ex.: relatório duplicado) para testar se o LLM mantém foco na tool correta.
Ferramenta/avaliação é meio para demonstrar o fenômeno, mas evitar escopo explosivo.
Estresse principal: informação no contexto para decidir a tool, não criar dezenas de tools.

8. Próximos passos (objetivos e rápidos)

A. Definir o MVP do experimento (1 hora)

Escolher 3 tools finais
Definir 4 níveis de poluição (0/20/40/60)
Definir 2 modelos para comparar

B. Fechar o template do prompt (1–2 horas)

Uma versão “limpa”
Uma versão “poluída”
Garantir que a pergunta exige get_stock_price

C. Implementar o script (1–2 dias)

runner + logs + evaluator simples
export CSV/JSON

D. Rodar e escrever resultados (1 dia)

gerar tabela de acertos por condição
1 gráfico de degradação

9. Checklist anti-escopo (para você não cair na armadilha do “hub” agora)

Se a feature não contribui diretamente para provar o fenômeno e gerar métrica no paper, ela fica fora do MVP. Exemplos a evitar agora:

UI completa com login, ranking, “blind mode” avançado, etc.
dezenas de provedores e integrações
modo de anotação manual muito sofisticado

Você pode mencionar tudo isso como trabalho futuro, e isso inclusive valoriza o texto.

Se você quiser, eu também posso pegar esse conteúdo e transformar em um documento único no formato de “Plano do Trabalho + Metodologia + Cronograma” (com seções prontas para colar no template do ITA/CEDS/SEDS), já com uma sugestão de cronograma por semana para janeiro–fevereiro.
resumo do achado e extensão futura (a plataforma/hub)
o que explica as falhas
limites do cenário e generalização
tabelas, gráficos, análise
exemplos qualitativos (1–2 casos clássicos)
arquitetura do script/ferramenta
logging e reprodutibilidade
cenário, tools, dataset sintético (relatórios duplicados)
variáveis (poluição, modelo)
métricas e critérios de sucesso
context rot / long context degradation
tool calling e falhas (alucinação, ancoragem)
avaliação de LLMs (overview)
Problema: contexto + tool calling
Motivação: segurança, confiabilidade, avaliação
Tabelas e 1–2 gráficos (curva de degradação)
Regra simples: se chamou tool correta → OK; senão → fail
Se respondeu com preço do relatório → “ancorou no contexto”
Executa N rodadas por condição (ex.: 20 execuções por nível)
Salva logs (prompt hash, tool calls, resposta final)
Entrada: pollution_level, base_report_text, question
Saída: prompt final com duplicações e “noise blocks”
gera prompts com diferentes níveis de “poluição” (0%, 20%, 40%…),
chama o(s) modelo(s),
registra se a tool correta foi chamada,
calcula métricas simples.
