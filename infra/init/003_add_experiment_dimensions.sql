-- =============================================================================
-- Migration: Novas dimensões experimentais (v3)
-- Adiciona tool_set, context_placement, adversarial_variant, tool_call tracking
-- =============================================================================

-- Novas colunas em executions
ALTER TABLE executions
ADD COLUMN IF NOT EXISTS tool_set VARCHAR(20) NOT NULL DEFAULT 'base',
ADD COLUMN IF NOT EXISTS context_placement VARCHAR(20) NOT NULL DEFAULT 'user',
ADD COLUMN IF NOT EXISTS adversarial_variant VARCHAR(20);

-- Constraints
ALTER TABLE executions ADD CONSTRAINT valid_tool_set
    CHECK (tool_set IN ('base', 'expanded'));
ALTER TABLE executions ADD CONSTRAINT valid_context_placement
    CHECK (context_placement IN ('user', 'system'));
ALTER TABLE executions ADD CONSTRAINT valid_adversarial_variant
    CHECK (adversarial_variant IS NULL OR adversarial_variant IN ('with_timestamp', 'without_timestamp'));

COMMENT ON COLUMN executions.tool_set IS 'Conjunto de tools usado (base=4, expanded=8)';
COMMENT ON COLUMN executions.context_placement IS 'Onde o contexto foi posicionado (user ou system prompt)';
COMMENT ON COLUMN executions.adversarial_variant IS 'Variante adversarial (com/sem timestamp). NULL se difficulty != adversarial';

-- Novas colunas em evaluations
ALTER TABLE evaluations
ADD COLUMN IF NOT EXISTS tool_call_count INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS tool_call_sequence TEXT;

COMMENT ON COLUMN evaluations.tool_call_count IS 'Número de tool calls realizadas na execução';
COMMENT ON COLUMN evaluations.tool_call_sequence IS 'Sequência de tool calls (arrow-separated, ex: get_current_datetime -> get_stock_price)';

-- Índices
CREATE INDEX IF NOT EXISTS idx_executions_tool_set ON executions(tool_set);
CREATE INDEX IF NOT EXISTS idx_executions_context_placement ON executions(context_placement);

-- Atualiza índice composto para incluir novas dimensões
DROP INDEX IF EXISTS idx_executions_analysis;
CREATE INDEX idx_executions_analysis
    ON executions(experiment_id, model_id, difficulty, tool_set, context_placement, pollution_level);

-- Novas tools no banco
INSERT INTO tools (name, description, parameters_schema, is_target, mock_response) VALUES
    ('get_stock_dividend_history', 'Obtém o histórico de dividendos pagos por uma ação.',
     '{"type":"object","properties":{"ticker":{"type":"string"}},"required":["ticker"]}', FALSE, NULL),
    ('get_analyst_rating', 'Obtém a recomendação e nota dos analistas para uma ação.',
     '{"type":"object","properties":{"ticker":{"type":"string"}},"required":["ticker"]}', FALSE, NULL),
    ('get_market_news', 'Busca as últimas notícias do mercado sobre uma ação.',
     '{"type":"object","properties":{"ticker":{"type":"string"}},"required":["ticker"]}', FALSE, NULL),
    ('get_current_datetime', 'Retorna a data e hora atuais do sistema.',
     '{"type":"object","properties":{},"required":[]}', FALSE, NULL)
ON CONFLICT (name) DO NOTHING;

-- Template v2 adversarial sem timestamp
INSERT INTO prompt_templates (name, description, system_prompt, user_prompt_template, context_template, expected_tool_id, variables_schema)
VALUES
    ('stock_price_adversarial_no_ts',
     'v2 Adversarial sem timestamp - Frase simulando dado real, sem data/hora',
     'Você é um assistente financeiro. Responda da melhor forma possível utilizando os recursos disponíveis.',
     'Qual o preço da ação {ticker}?',
     NULL,
     (SELECT id FROM tools WHERE name = 'get_stock_price'),
     '{}')
ON CONFLICT (name) DO NOTHING;

-- =============================================================================
-- Recria views para incluir novas dimensões
-- =============================================================================

DROP VIEW IF EXISTS v_model_comparison CASCADE;
DROP VIEW IF EXISTS v_metrics_by_pollution CASCADE;
DROP VIEW IF EXISTS v_experiment_results CASCADE;

-- View: Resultados consolidados (com novas dimensões)
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

-- View: Métricas agregadas por dimensões
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

-- View: Comparação entre modelos (com novas dimensões)
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
