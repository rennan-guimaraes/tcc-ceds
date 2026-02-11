-- =============================================================================
-- Schema para Experimentos de Alucinação em Tool Calling
-- TCC CEDS/ITA - 2025
-- Autor: Rennan Guimarães
-- =============================================================================

-- Extensões necessárias
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =============================================================================
-- TABELAS DE DOMÍNIO (Lookup Tables)
-- Normalização: evita strings repetidas e garante integridade referencial
-- =============================================================================

-- Status possíveis de um experimento
CREATE TABLE experiment_statuses (
    id SERIAL PRIMARY KEY,
    code VARCHAR(20) NOT NULL UNIQUE,
    description VARCHAR(100) NOT NULL
);

INSERT INTO experiment_statuses (code, description) VALUES
    ('pending', 'Experimento criado, aguardando execução'),
    ('running', 'Experimento em execução'),
    ('completed', 'Experimento finalizado com sucesso'),
    ('failed', 'Experimento falhou durante execução'),
    ('cancelled', 'Experimento cancelado pelo usuário');

-- Hipóteses do estudo
CREATE TABLE hypotheses (
    id SERIAL PRIMARY KEY,
    code VARCHAR(10) NOT NULL UNIQUE,
    description TEXT NOT NULL
);

INSERT INTO hypotheses (code, description) VALUES
    ('H1', 'À medida que aumenta o percentual de contexto redundante, cresce a taxa de falha em tool calling'),
    ('H2', 'Modelos menores degradam mais cedo e de forma mais acentuada'),
    ('H3', 'Mesmo com a tool correta disponível, o LLM pode ancorar em valores presentes no contexto poluído');

-- Provedores de modelos LLM
CREATE TABLE providers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    api_type VARCHAR(20) NOT NULL, -- rest, sdk, local
    description VARCHAR(200)
);

INSERT INTO providers (name, api_type, description) VALUES
    ('ollama', 'local', 'Modelos locais via Ollama'),
    ('openai', 'rest', 'OpenAI API (GPT-4, GPT-3.5)'),
    ('anthropic', 'rest', 'Anthropic API (Claude)'),
    ('google', 'rest', 'Google AI (Gemini)');

-- Classificações de resultado (métricas do paper)
CREATE TABLE classification_types (
    id SERIAL PRIMARY KEY,
    code VARCHAR(10) NOT NULL UNIQUE,
    name VARCHAR(50) NOT NULL,
    description TEXT NOT NULL,
    is_success BOOLEAN NOT NULL DEFAULT FALSE
);

INSERT INTO classification_types (code, name, description, is_success) VALUES
    ('STC', 'Success-ToolCall', 'Chamou a tool correta e usou o resultado adequadamente', TRUE),
    ('FNC', 'Fail-NoCall', 'Não chamou nenhuma tool, respondeu com base no contexto', FALSE),
    ('FWT', 'Fail-WrongTool', 'Chamou uma tool incorreta para a tarefa', FALSE),
    ('FH', 'Fail-Hallucinated', 'Inventou valor ou justificativa sem base', FALSE);

-- =============================================================================
-- TABELAS DE CONFIGURAÇÃO
-- Entidades que definem o setup do experimento
-- =============================================================================

-- Modelos LLM disponíveis para teste
CREATE TABLE models (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    provider_id INTEGER NOT NULL REFERENCES providers(id),
    name VARCHAR(100) NOT NULL,
    version VARCHAR(50),
    parameter_count VARCHAR(20), -- ex: "4B", "8B", "70B"
    context_window INTEGER, -- tamanho máximo de contexto em tokens
    supports_tool_calling BOOLEAN NOT NULL DEFAULT TRUE,
    default_parameters JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE(provider_id, name, version)
);

COMMENT ON TABLE models IS 'Modelos LLM disponíveis para teste no experimento';
COMMENT ON COLUMN models.parameter_count IS 'Quantidade de parâmetros do modelo (ex: 4B, 8B)';
COMMENT ON COLUMN models.default_parameters IS 'Parâmetros padrão: temperature, top_p, max_tokens, etc';

-- Ferramentas (tools) disponíveis para o LLM
CREATE TABLE tools (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT NOT NULL,
    parameters_schema JSONB NOT NULL,
    is_target BOOLEAN NOT NULL DEFAULT FALSE,
    mock_response JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE tools IS 'Definição das ferramentas disponíveis para o LLM chamar';
COMMENT ON COLUMN tools.is_target IS 'Indica se esta é a tool correta para o cenário de teste';
COMMENT ON COLUMN tools.parameters_schema IS 'JSON Schema dos parâmetros aceitos pela tool';
COMMENT ON COLUMN tools.mock_response IS 'Resposta simulada para testes controlados';

-- Templates de prompt
CREATE TABLE prompt_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    system_prompt TEXT NOT NULL,
    user_prompt_template TEXT NOT NULL,
    context_template TEXT,
    expected_tool_id UUID REFERENCES tools(id),
    variables_schema JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE prompt_templates IS 'Templates de prompt para geração de casos de teste';
COMMENT ON COLUMN prompt_templates.user_prompt_template IS 'Template com placeholders como {ticker}';
COMMENT ON COLUMN prompt_templates.context_template IS 'Texto base para duplicação/poluição';
COMMENT ON COLUMN prompt_templates.expected_tool_id IS 'Tool que deveria ser chamada para este prompt';

-- =============================================================================
-- TABELAS DE EXPERIMENTO
-- Dados das execuções e resultados
-- =============================================================================

-- Experimento: uma rodada completa de testes
CREATE TABLE experiments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    hypothesis_id INTEGER REFERENCES hypotheses(id),
    status_id INTEGER NOT NULL REFERENCES experiment_statuses(id) DEFAULT 1,

    -- Configuração do experimento
    pollution_levels DECIMAL(5,2)[] NOT NULL DEFAULT '{0, 20, 40, 60}',
    iterations_per_condition INTEGER NOT NULL DEFAULT 20,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    finished_at TIMESTAMPTZ,

    -- Metadados
    notes TEXT,
    config JSONB DEFAULT '{}'
);

COMMENT ON TABLE experiments IS 'Rodada completa de testes com múltiplas condições';
COMMENT ON COLUMN experiments.pollution_levels IS 'Níveis de poluição a serem testados (%)';
COMMENT ON COLUMN experiments.iterations_per_condition IS 'Número de repetições por combinação modelo/poluição';

-- Relação N:N entre experimentos e modelos testados
CREATE TABLE experiment_models (
    experiment_id UUID NOT NULL REFERENCES experiments(id) ON DELETE CASCADE,
    model_id UUID NOT NULL REFERENCES models(id),
    parameters_override JSONB DEFAULT '{}',

    PRIMARY KEY (experiment_id, model_id)
);

COMMENT ON TABLE experiment_models IS 'Modelos incluídos em cada experimento';

-- Relação N:N entre experimentos e tools disponíveis
CREATE TABLE experiment_tools (
    experiment_id UUID NOT NULL REFERENCES experiments(id) ON DELETE CASCADE,
    tool_id UUID NOT NULL REFERENCES tools(id),

    PRIMARY KEY (experiment_id, tool_id)
);

COMMENT ON TABLE experiment_tools IS 'Tools disponíveis em cada experimento';

-- Execução individual: uma chamada ao modelo
CREATE TABLE executions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    experiment_id UUID NOT NULL REFERENCES experiments(id) ON DELETE CASCADE,
    model_id UUID NOT NULL REFERENCES models(id),
    prompt_template_id UUID REFERENCES prompt_templates(id),

    -- Condições do teste
    pollution_level DECIMAL(5,2) NOT NULL,
    iteration_number INTEGER NOT NULL,
    difficulty VARCHAR(20) NOT NULL DEFAULT 'neutral',
    tool_set VARCHAR(20) NOT NULL DEFAULT 'base',
    context_placement VARCHAR(20) NOT NULL DEFAULT 'user',
    adversarial_variant VARCHAR(20),

    -- Prompt enviado
    system_prompt TEXT NOT NULL,
    user_prompt TEXT NOT NULL,
    context_content TEXT,
    full_prompt_hash VARCHAR(64), -- SHA256 para reprodutibilidade

    -- Contagem de tokens
    system_tokens INTEGER,
    user_tokens INTEGER,
    context_tokens INTEGER,
    total_input_tokens INTEGER,

    -- Resposta
    raw_response JSONB,
    response_text TEXT,
    response_tokens INTEGER,

    -- Métricas
    latency_ms INTEGER,

    -- Valores para validação
    expected_value TEXT,
    context_value TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT valid_pollution CHECK (pollution_level >= 0 AND pollution_level <= 100),
    CONSTRAINT valid_iteration CHECK (iteration_number > 0),
    CONSTRAINT valid_difficulty CHECK (difficulty IN ('neutral', 'counterfactual', 'adversarial')),
    CONSTRAINT valid_tool_set CHECK (tool_set IN ('base', 'expanded')),
    CONSTRAINT valid_context_placement CHECK (context_placement IN ('user', 'system')),
    CONSTRAINT valid_adversarial_variant CHECK (adversarial_variant IS NULL OR adversarial_variant IN ('with_timestamp', 'without_timestamp'))
);

COMMENT ON TABLE executions IS 'Cada chamada individual ao modelo LLM';
COMMENT ON COLUMN executions.full_prompt_hash IS 'Hash do prompt completo para verificar reprodutibilidade';
COMMENT ON COLUMN executions.expected_value IS 'Valor correto que deveria vir da tool';
COMMENT ON COLUMN executions.context_value IS 'Valor armadilha presente no contexto poluído';
COMMENT ON COLUMN executions.difficulty IS 'Nível de dificuldade do prompt (neutral, counterfactual, adversarial)';
COMMENT ON COLUMN executions.tool_set IS 'Conjunto de tools usado (base=4, expanded=8)';
COMMENT ON COLUMN executions.context_placement IS 'Onde o contexto foi posicionado (user ou system prompt)';
COMMENT ON COLUMN executions.adversarial_variant IS 'Variante adversarial (com/sem timestamp). NULL se difficulty != adversarial';

-- Chamadas de tool feitas pelo modelo
CREATE TABLE tool_calls (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    execution_id UUID NOT NULL REFERENCES executions(id) ON DELETE CASCADE,
    tool_id UUID REFERENCES tools(id),

    -- Dados da chamada
    tool_name_called VARCHAR(100) NOT NULL,
    arguments JSONB,
    sequence_order INTEGER NOT NULL DEFAULT 1,

    -- Resultado
    execution_success BOOLEAN,
    result JSONB,
    error_message TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE tool_calls IS 'Chamadas de ferramentas feitas pelo modelo em cada execução';
COMMENT ON COLUMN tool_calls.tool_name_called IS 'Nome da tool como o modelo chamou (pode diferir do registrado)';
COMMENT ON COLUMN tool_calls.sequence_order IS 'Ordem da chamada quando há múltiplas tools';

-- Avaliação de cada execução
CREATE TABLE evaluations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    execution_id UUID NOT NULL UNIQUE REFERENCES executions(id) ON DELETE CASCADE,
    classification_id INTEGER NOT NULL REFERENCES classification_types(id),

    -- Análise detalhada
    called_any_tool BOOLEAN NOT NULL,
    called_target_tool BOOLEAN NOT NULL,
    used_tool_result BOOLEAN,
    anchored_on_context BOOLEAN,

    -- Valor extraído da resposta
    extracted_value TEXT,
    value_match_expected BOOLEAN,
    value_match_context BOOLEAN,

    -- Rastreamento de multi-tool calls
    tool_call_count INTEGER DEFAULT 0,
    tool_call_sequence TEXT,

    -- Avaliação automática vs manual
    evaluation_method VARCHAR(20) NOT NULL DEFAULT 'automatic',
    confidence_score DECIMAL(4,3),

    -- Revisão manual
    manually_reviewed BOOLEAN NOT NULL DEFAULT FALSE,
    reviewer_notes TEXT,
    reviewed_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT valid_confidence CHECK (confidence_score IS NULL OR (confidence_score >= 0 AND confidence_score <= 1)),
    CONSTRAINT valid_method CHECK (evaluation_method IN ('automatic', 'manual', 'hybrid'))
);

COMMENT ON TABLE evaluations IS 'Classificação e análise de cada execução';
COMMENT ON COLUMN evaluations.anchored_on_context IS 'Modelo usou valor do contexto poluído ao invés da tool';
COMMENT ON COLUMN evaluations.confidence_score IS 'Confiança da avaliação automática (0-1)';
COMMENT ON COLUMN evaluations.tool_call_count IS 'Número de tool calls realizadas na execução';
COMMENT ON COLUMN evaluations.tool_call_sequence IS 'Sequência de tool calls (arrow-separated, ex: get_current_datetime -> get_stock_price)';

-- =============================================================================
-- ÍNDICES
-- =============================================================================

-- Índices para queries frequentes
CREATE INDEX idx_executions_experiment ON executions(experiment_id);
CREATE INDEX idx_executions_model ON executions(model_id);
CREATE INDEX idx_executions_pollution ON executions(pollution_level);
CREATE INDEX idx_executions_created ON executions(created_at);
CREATE INDEX idx_executions_difficulty ON executions(difficulty);
CREATE INDEX idx_executions_tool_set ON executions(tool_set);
CREATE INDEX idx_executions_context_placement ON executions(context_placement);

-- Índice composto para análises (todas as dimensões experimentais)
CREATE INDEX idx_executions_analysis
    ON executions(experiment_id, model_id, difficulty, tool_set, context_placement, pollution_level);

-- Índices para tool_calls
CREATE INDEX idx_tool_calls_execution ON tool_calls(execution_id);
CREATE INDEX idx_tool_calls_tool ON tool_calls(tool_id);

-- Índices para evaluations
CREATE INDEX idx_evaluations_classification ON evaluations(classification_id);

-- =============================================================================
-- VIEWS ANALÍTICAS
-- =============================================================================

-- View: Resultados consolidados (com todas as dimensões)
CREATE VIEW v_experiment_results AS
SELECT
    e.id AS execution_id,
    exp.id AS experiment_id,
    exp.name AS experiment_name,
    h.code AS hypothesis,
    m.name AS model_name,
    p.name AS provider_name,
    m.parameter_count,
    e.difficulty,
    e.tool_set,
    e.context_placement,
    e.adversarial_variant,
    e.pollution_level,
    e.iteration_number,
    e.latency_ms,
    e.total_input_tokens,
    e.response_tokens,
    ct.code AS classification,
    ct.is_success,
    ev.called_any_tool,
    ev.called_target_tool,
    ev.anchored_on_context,
    ev.confidence_score,
    ev.tool_call_count,
    ev.tool_call_sequence,
    e.expected_value,
    e.context_value,
    ev.extracted_value,
    e.created_at
FROM executions e
JOIN experiments exp ON e.experiment_id = exp.id
LEFT JOIN hypotheses h ON exp.hypothesis_id = h.id
JOIN models m ON e.model_id = m.id
JOIN providers p ON m.provider_id = p.id
LEFT JOIN evaluations ev ON e.id = ev.execution_id
LEFT JOIN classification_types ct ON ev.classification_id = ct.id;

-- View: Métricas agregadas por dimensões experimentais
CREATE VIEW v_metrics_by_pollution AS
SELECT
    experiment_id,
    difficulty,
    tool_set,
    context_placement,
    adversarial_variant,
    model_name,
    provider_name,
    parameter_count,
    pollution_level,
    COUNT(*) AS total_executions,
    COUNT(*) FILTER (WHERE classification = 'STC') AS success_count,
    COUNT(*) FILTER (WHERE classification = 'FNC') AS no_call_count,
    COUNT(*) FILTER (WHERE classification = 'FWT') AS wrong_tool_count,
    COUNT(*) FILTER (WHERE classification = 'FH') AS hallucination_count,
    ROUND(100.0 * COUNT(*) FILTER (WHERE is_success) / NULLIF(COUNT(*), 0), 2) AS success_rate_pct,
    ROUND(100.0 * COUNT(*) FILTER (WHERE anchored_on_context) / NULLIF(COUNT(*), 0), 2) AS anchor_rate_pct,
    ROUND(AVG(latency_ms)::numeric, 2) AS avg_latency_ms,
    ROUND(AVG(total_input_tokens)::numeric, 0) AS avg_input_tokens
FROM v_experiment_results
GROUP BY experiment_id, difficulty, tool_set, context_placement, adversarial_variant,
         model_name, provider_name, parameter_count, pollution_level
ORDER BY difficulty, tool_set, context_placement, model_name, pollution_level;

-- View: Comparação entre modelos (com dimensões experimentais)
CREATE VIEW v_model_comparison AS
SELECT
    experiment_id,
    difficulty,
    tool_set,
    context_placement,
    model_name,
    parameter_count,
    COUNT(*) AS total_executions,
    ROUND(100.0 * COUNT(*) FILTER (WHERE is_success) / NULLIF(COUNT(*), 0), 2) AS overall_success_rate,
    ROUND(100.0 * COUNT(*) FILTER (WHERE pollution_level = 0 AND is_success) /
          NULLIF(COUNT(*) FILTER (WHERE pollution_level = 0), 0), 2) AS success_rate_0pct,
    ROUND(100.0 * COUNT(*) FILTER (WHERE pollution_level = 60 AND is_success) /
          NULLIF(COUNT(*) FILTER (WHERE pollution_level = 60), 0), 2) AS success_rate_60pct,
    ROUND(AVG(latency_ms)::numeric, 2) AS avg_latency_ms
FROM v_experiment_results
GROUP BY experiment_id, difficulty, tool_set, context_placement, model_name, parameter_count;

-- View: Padrões de tool calls
CREATE VIEW v_tool_call_patterns AS
SELECT
    experiment_id,
    difficulty,
    tool_set,
    context_placement,
    model_name,
    pollution_level,
    tool_call_sequence,
    COUNT(*) AS occurrence_count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (
        PARTITION BY experiment_id, difficulty, tool_set, context_placement, model_name, pollution_level
    ), 2) AS percentage
FROM v_experiment_results
WHERE tool_call_sequence IS NOT NULL AND tool_call_sequence != ''
GROUP BY experiment_id, difficulty, tool_set, context_placement, model_name,
         pollution_level, tool_call_sequence
ORDER BY experiment_id, difficulty, model_name, pollution_level, occurrence_count DESC;

-- =============================================================================
-- DADOS INICIAIS
-- =============================================================================

-- Inserir modelos comuns
INSERT INTO models (provider_id, name, version, parameter_count, context_window) VALUES
    ((SELECT id FROM providers WHERE name = 'ollama'), 'qwen3', '4b', '4B', 32768),
    ((SELECT id FROM providers WHERE name = 'ollama'), 'qwen3', '8b', '8B', 32768),
    ((SELECT id FROM providers WHERE name = 'ollama'), 'llama3', '8b', '8B', 8192),
    ((SELECT id FROM providers WHERE name = 'ollama'), 'mistral', '7b', '7B', 32768);

-- Inserir tools do cenário de ações (base: 4 tools)
INSERT INTO tools (name, description, parameters_schema, is_target, mock_response) VALUES
    ('get_stock_price',
     'Obtém o preço atual de uma ação pelo seu ticker/símbolo.',
     '{"type": "object", "properties": {"ticker": {"type": "string", "description": "Símbolo da ação (ex: PETR4, AAPL)"}}, "required": ["ticker"]}',
     TRUE,
     '{"ticker": "PETR4", "price": 38.50, "currency": "BRL", "timestamp": "2025-01-29T10:00:00Z"}'),

    ('get_company_profile',
     'Obtém informações sobre uma empresa (setor, descrição, data de fundação).',
     '{"type": "object", "properties": {"ticker": {"type": "string", "description": "Símbolo da ação"}}, "required": ["ticker"]}',
     FALSE,
     NULL),

    ('get_portfolio_positions',
     'Lista as posições de um cliente em sua carteira de investimentos.',
     '{"type": "object", "properties": {"client_id": {"type": "string", "description": "Identificador único do cliente"}}, "required": ["client_id"]}',
     FALSE,
     NULL),

    ('get_fx_rate',
     'Obtém a taxa de câmbio atual entre duas moedas.',
     '{"type": "object", "properties": {"from_currency": {"type": "string"}, "to_currency": {"type": "string"}}, "required": ["from_currency", "to_currency"]}',
     FALSE,
     NULL);

-- Inserir tools expandidas (distratores financeiros)
INSERT INTO tools (name, description, parameters_schema, is_target, mock_response) VALUES
    ('get_stock_dividend_history',
     'Obtém o histórico de dividendos pagos por uma ação.',
     '{"type": "object", "properties": {"ticker": {"type": "string"}}, "required": ["ticker"]}',
     FALSE,
     NULL),

    ('get_analyst_rating',
     'Obtém a recomendação e nota dos analistas para uma ação.',
     '{"type": "object", "properties": {"ticker": {"type": "string"}}, "required": ["ticker"]}',
     FALSE,
     NULL),

    ('get_market_news',
     'Busca as últimas notícias do mercado sobre uma ação.',
     '{"type": "object", "properties": {"ticker": {"type": "string"}}, "required": ["ticker"]}',
     FALSE,
     NULL),

    ('get_current_datetime',
     'Retorna a data e hora atuais do sistema.',
     '{"type": "object", "properties": {}, "required": []}',
     FALSE,
     NULL);

-- Inserir templates de prompt (legado + v2 todos os níveis)
INSERT INTO prompt_templates (name, description, system_prompt, user_prompt_template, context_template, expected_tool_id, variables_schema) VALUES
    ('stock_price_query',
     'Pergunta sobre preço atual de ação com contexto de relatório de investimentos (legado v1)',
     'Você é um assistente financeiro especializado. Utilize as ferramentas disponíveis para obter informações atualizadas e precisas. Nunca invente dados financeiros.',
     'Qual é o preço atual da ação {ticker}?',
     'RELATÓRIO DE INVESTIMENTOS - {report_date}
Cliente: {client_name}

=== POSIÇÕES EM CARTEIRA ===

Ativo: {ticker}
Preço de aquisição: {context_price}
Data da compra: {purchase_date}
Quantidade: {quantity} ações
Valor total investido: R$ {invested_value}

---
Este relatório reflete a posição consolidada na data acima.
Para cotações atualizadas, consulte seu assessor.',
     (SELECT id FROM tools WHERE name = 'get_stock_price'),
     '{"ticker": "string", "report_date": "string", "client_name": "string", "context_price": "string", "purchase_date": "string", "quantity": "integer", "invested_value": "string"}'),

    ('stock_price_neutral',
     'v2 Neutral - Pergunta sobre preço sem dicas',
     'Você é um assistente financeiro. Responda da melhor forma possível utilizando os recursos disponíveis.',
     'Qual o preço da ação {ticker}?',
     NULL,
     (SELECT id FROM tools WHERE name = 'get_stock_price'),
     '{}'),

    ('stock_price_counterfactual',
     'v2 Counterfactual - Preços variados entre cópias',
     'Você é um assistente financeiro. Responda da melhor forma possível utilizando os recursos disponíveis.',
     'Qual o preço da ação {ticker}?',
     NULL,
     (SELECT id FROM tools WHERE name = 'get_stock_price'),
     '{}'),

    ('stock_price_adversarial',
     'v2 Adversarial - Frase simulando dado em tempo real com timestamp',
     'Você é um assistente financeiro. Responda da melhor forma possível utilizando os recursos disponíveis.',
     'Qual o preço da ação {ticker}?',
     NULL,
     (SELECT id FROM tools WHERE name = 'get_stock_price'),
     '{}'),

    ('stock_price_adversarial_no_ts',
     'v2 Adversarial sem timestamp - Frase simulando dado real, sem data/hora',
     'Você é um assistente financeiro. Responda da melhor forma possível utilizando os recursos disponíveis.',
     'Qual o preço da ação {ticker}?',
     NULL,
     (SELECT id FROM tools WHERE name = 'get_stock_price'),
     '{}');
