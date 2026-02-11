"""Repositório para persistência de dados do experimento.

Implementa operações CRUD para salvar e recuperar dados
das execuções e avaliações no PostgreSQL.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any
from uuid import UUID

from tcc_experiment.database.connection import get_connection

if TYPE_CHECKING:
    from tcc_experiment.evaluator.classifier import EvaluationResult
    from tcc_experiment.prompt.generator import GeneratedPrompt
    from tcc_experiment.runner.base import RunnerResult


class ExperimentRepository:
    """Repositório para operações de experimento.

    Gerencia a persistência de experimentos, execuções e avaliações
    no banco de dados PostgreSQL.

    Example:
        >>> repo = ExperimentRepository()
        >>> exp_id = repo.create_experiment("Teste H1", "H1")
        >>> repo.save_execution(exp_id, model_id, prompt, result, evaluation)
    """

    def create_experiment(
        self,
        name: str,
        hypothesis: str | None = None,
        description: str | None = None,
        pollution_levels: list[float] | None = None,
        iterations: int = 20,
    ) -> UUID:
        """Cria um novo experimento.

        Args:
            name: Nome do experimento.
            hypothesis: Código da hipótese (H1, H2, H3).
            description: Descrição detalhada.
            pollution_levels: Níveis de poluição a testar.
            iterations: Iterações por condição.

        Returns:
            UUID do experimento criado.
        """
        if pollution_levels is None:
            pollution_levels = [0.0, 20.0, 40.0, 60.0]

        with get_connection() as conn, conn.cursor() as cur:
            # Busca IDs de referência
            hypothesis_id = None
            if hypothesis:
                cur.execute(
                    "SELECT id FROM hypotheses WHERE code = %s",
                    (hypothesis,)
                )
                row = cur.fetchone()
                if row:
                    hypothesis_id = row["id"]

            # Cria experimento
            cur.execute(
                """
                    INSERT INTO experiments (
                        name, description, hypothesis_id,
                        pollution_levels, iterations_per_condition
                    )
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                (name, description, hypothesis_id, pollution_levels, iterations)
            )
            result = cur.fetchone()
            conn.commit()
            return result["id"]

    def start_experiment(self, experiment_id: UUID) -> None:
        """Marca experimento como em execução.

        Args:
            experiment_id: ID do experimento.
        """
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE experiments
                    SET status_id = (SELECT id FROM experiment_statuses WHERE code = 'running'),
                        started_at = NOW()
                    WHERE id = %s
                    """,
                    (experiment_id,)
                )
                conn.commit()

    def finish_experiment(
        self,
        experiment_id: UUID,
        status: str = "completed"
    ) -> None:
        """Marca experimento como finalizado.

        Args:
            experiment_id: ID do experimento.
            status: Status final (completed, failed, cancelled).
        """
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE experiments
                    SET status_id = (SELECT id FROM experiment_statuses WHERE code = %s),
                        finished_at = NOW()
                    WHERE id = %s
                    """,
                    (status, experiment_id)
                )
                conn.commit()

    def get_or_create_model(
        self,
        name: str,
        provider: str = "ollama",
        version: str | None = None,
        parameter_count: str | None = None,
    ) -> UUID:
        """Obtém ou cria um modelo.

        Args:
            name: Nome do modelo.
            provider: Nome do provedor.
            version: Versão do modelo.
            parameter_count: Quantidade de parâmetros.

        Returns:
            UUID do modelo.
        """
        with get_connection() as conn, conn.cursor() as cur:
            # Tenta encontrar modelo existente (incluindo versão)
            if version:
                cur.execute(
                    """
                        SELECT m.id FROM models m
                        JOIN providers p ON m.provider_id = p.id
                        WHERE m.name = %s AND p.name = %s AND m.version = %s
                        """,
                    (name, provider, version)
                )
            else:
                cur.execute(
                    """
                        SELECT m.id FROM models m
                        JOIN providers p ON m.provider_id = p.id
                        WHERE m.name = %s AND p.name = %s AND m.version IS NULL
                        """,
                    (name, provider)
                )
            row = cur.fetchone()
            if row:
                return row["id"]

            # Cria novo modelo
            cur.execute(
                """
                    INSERT INTO models (provider_id, name, version, parameter_count)
                    SELECT p.id, %s, %s, %s
                    FROM providers p WHERE p.name = %s
                    RETURNING id
                    """,
                (name, version, parameter_count, provider)
            )
            result = cur.fetchone()
            conn.commit()
            return result["id"]

    def get_prompt_template_id(self, name: str = "stock_price_query") -> UUID | None:
        """Obtém ID de um template de prompt.

        Args:
            name: Nome do template.

        Returns:
            UUID do template ou None.
        """
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute(
                "SELECT id FROM prompt_templates WHERE name = %s",
                (name,)
            )
            row = cur.fetchone()
            return row["id"] if row else None

    def save_execution(
        self,
        experiment_id: UUID,
        model_id: UUID,
        prompt: GeneratedPrompt,
        result: RunnerResult,
        evaluation: EvaluationResult,
        iteration: int,
        difficulty: str = "neutral",
        tool_set: str = "base",
        context_placement: str = "user",
        adversarial_variant: str | None = None,
    ) -> UUID:
        """Salva uma execução completa com avaliação.

        Args:
            experiment_id: ID do experimento.
            model_id: ID do modelo.
            prompt: Prompt gerado.
            result: Resultado da execução.
            evaluation: Avaliação do resultado.
            iteration: Número da iteração.
            difficulty: Nível de dificuldade.
            tool_set: Conjunto de tools usado.
            context_placement: Onde o contexto foi posicionado.
            adversarial_variant: Variante adversarial (None se não adversarial).

        Returns:
            UUID da execução criada.
        """
        with get_connection() as conn:
            with conn.cursor() as cur:
                # Obtém template ID
                template_id = self.get_prompt_template_id(prompt.template_name)

                # Insere execução
                cur.execute(
                    """
                    INSERT INTO executions (
                        experiment_id, model_id, prompt_template_id,
                        pollution_level, iteration_number,
                        difficulty, tool_set, context_placement, adversarial_variant,
                        system_prompt, user_prompt, context_content,
                        full_prompt_hash,
                        raw_response, response_text,
                        latency_ms,
                        expected_value, context_value
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (
                        experiment_id,
                        model_id,
                        template_id,
                        prompt.pollution_level,
                        iteration,
                        difficulty,
                        tool_set,
                        context_placement,
                        adversarial_variant,
                        prompt.system_prompt,
                        prompt.user_prompt,
                        prompt.context,
                        prompt.prompt_hash,
                        json.dumps(result.raw_response) if result.raw_response else None,
                        result.response_text,
                        result.latency_ms,
                        prompt.expected_value,
                        prompt.context_value,
                    )
                )
                execution_row = cur.fetchone()
                execution_id = execution_row["id"]

                # Insere tool calls
                for tc in result.tool_calls:
                    # Tenta encontrar tool_id
                    cur.execute(
                        "SELECT id FROM tools WHERE name = %s",
                        (tc.tool_name,)
                    )
                    tool_row = cur.fetchone()
                    tool_id = tool_row["id"] if tool_row else None

                    cur.execute(
                        """
                        INSERT INTO tool_calls (
                            execution_id, tool_id, tool_name_called,
                            arguments, sequence_order, result, error_message
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """,
                        (
                            execution_id,
                            tool_id,
                            tc.tool_name,
                            json.dumps(tc.arguments) if tc.arguments else None,
                            tc.sequence_order,
                            json.dumps(tc.result) if tc.result else None,
                            tc.error,
                        )
                    )

                # Insere avaliação
                cur.execute(
                    """
                    INSERT INTO evaluations (
                        execution_id, classification_id,
                        called_any_tool, called_target_tool,
                        used_tool_result, anchored_on_context,
                        extracted_value,
                        evaluation_method, confidence_score,
                        reviewer_notes,
                        tool_call_count, tool_call_sequence
                    )
                    SELECT %s, ct.id, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    FROM classification_types ct WHERE ct.code = %s
                    """,
                    (
                        execution_id,
                        evaluation.called_any_tool,
                        evaluation.called_target_tool,
                        evaluation.used_tool_result,
                        evaluation.anchored_on_context,
                        evaluation.extracted_value,
                        "automatic",
                        evaluation.confidence_score,
                        evaluation.reasoning,
                        evaluation.tool_call_count,
                        evaluation.tool_call_sequence,
                        evaluation.classification.value,
                    )
                )

                conn.commit()
                return execution_id

    def get_experiment_summary(self, experiment_id: UUID) -> dict[str, Any]:
        """Obtém resumo de um experimento.

        Args:
            experiment_id: ID do experimento.

        Returns:
            Dicionário com estatísticas do experimento.
        """
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute(
                """
                    SELECT * FROM v_metrics_by_pollution
                    WHERE experiment_id = %s
                    ORDER BY model_name, pollution_level
                    """,
                (experiment_id,)
            )
            return cur.fetchall()

    def get_experiment_results(self, experiment_id: UUID) -> list[dict[str, Any]]:
        """Obtém todos os resultados de um experimento.

        Args:
            experiment_id: ID do experimento.

        Returns:
            Lista de resultados.
        """
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute(
                """
                    SELECT * FROM v_experiment_results
                    WHERE experiment_id = %s
                    ORDER BY pollution_level, iteration_number
                    """,
                (experiment_id,)
            )
            return cur.fetchall()
