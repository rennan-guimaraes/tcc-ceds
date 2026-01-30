"""Classificador automático de resultados.

Classifica cada execução em uma das categorias:
- STC (Success-ToolCall): chamou a tool correta e usou o resultado
- FNC (Fail-NoCall): não chamou nenhuma tool
- FWT (Fail-WrongTool): chamou tool errada
- FH (Fail-Hallucinated): inventou valor sem base
"""

import re
from dataclasses import dataclass
from typing import Any

from tcc_experiment.database.models import Classification
from tcc_experiment.prompt.generator import GeneratedPrompt
from tcc_experiment.runner.base import RunnerResult


@dataclass
class EvaluationResult:
    """Resultado da avaliação de uma execução.

    Attributes:
        classification: Classificação (STC, FNC, FWT, FH).
        called_any_tool: Se alguma tool foi chamada.
        called_target_tool: Se a tool correta foi chamada.
        used_tool_result: Se usou o resultado da tool na resposta.
        anchored_on_context: Se usou valor do contexto poluído.
        extracted_value: Valor monetário extraído da resposta.
        confidence_score: Confiança na classificação (0-1).
        reasoning: Explicação da classificação.
    """

    classification: Classification
    called_any_tool: bool
    called_target_tool: bool
    used_tool_result: bool
    anchored_on_context: bool
    extracted_value: str | None
    confidence_score: float
    reasoning: str


class ResultClassifier:
    """Classificador automático de resultados de execução.

    Analisa os resultados de uma execução e classifica em uma
    das categorias definidas para o experimento.

    Example:
        >>> classifier = ResultClassifier()
        >>> evaluation = classifier.evaluate(prompt, result)
        >>> print(evaluation.classification)
        Classification.STC
    """

    # Padrões para extrair valores monetários
    MONEY_PATTERNS = [
        r"R\$\s*(\d+[.,]\d{2})",  # R$ 38,50 ou R$ 38.50
        r"(\d+[.,]\d{2})\s*(?:reais|BRL)",  # 38,50 reais ou 38.50 BRL
        r"preço[^0-9]*(\d+[.,]\d{2})",  # preço ... 38,50
        r"cotação[^0-9]*(\d+[.,]\d{2})",  # cotação ... 38,50
        r"(\d+[.,]\d{2})\s*(?:\(BRL\)|\(R\$\))",  # 38.50 (BRL)
        r"\*\*R\$\s*(\d+[.,]\d{2})\*\*",  # **R$ 38,50** (markdown bold)
    ]

    def __init__(self, target_tool: str = "get_stock_price") -> None:
        """Inicializa o classificador.

        Args:
            target_tool: Nome da tool correta para o cenário.
        """
        self.target_tool = target_tool

    def evaluate(
        self,
        prompt: GeneratedPrompt,
        result: RunnerResult,
    ) -> EvaluationResult:
        """Avalia uma execução e retorna a classificação.

        Args:
            prompt: Prompt que foi executado.
            result: Resultado da execução.

        Returns:
            EvaluationResult com a classificação e análise.
        """
        # Extrai informações básicas
        called_any_tool = result.called_any_tool
        called_target_tool = self.target_tool in result.called_tools_names

        # Extrai valor da resposta
        extracted_value = self._extract_monetary_value(result.response_text or "")

        # Normaliza valores para comparação
        expected_normalized = self._normalize_value(prompt.expected_value)
        context_normalized = self._normalize_value(prompt.context_value)
        extracted_normalized = self._normalize_value(extracted_value) if extracted_value else None

        # Verifica se usou valor da tool ou do contexto
        used_tool_result = (
            extracted_normalized is not None
            and expected_normalized is not None
            and self._values_match(extracted_normalized, expected_normalized)
        )

        anchored_on_context = (
            extracted_normalized is not None
            and context_normalized is not None
            and self._values_match(extracted_normalized, context_normalized)
            and not used_tool_result  # Só conta como ancoragem se não usou o correto
        )

        # Classifica
        classification, confidence, reasoning = self._classify(
            called_any_tool=called_any_tool,
            called_target_tool=called_target_tool,
            used_tool_result=used_tool_result,
            anchored_on_context=anchored_on_context,
            extracted_value=extracted_value,
            response_text=result.response_text or "",
        )

        return EvaluationResult(
            classification=classification,
            called_any_tool=called_any_tool,
            called_target_tool=called_target_tool,
            used_tool_result=used_tool_result,
            anchored_on_context=anchored_on_context,
            extracted_value=extracted_value,
            confidence_score=confidence,
            reasoning=reasoning,
        )

    def _classify(
        self,
        called_any_tool: bool,
        called_target_tool: bool,
        used_tool_result: bool,
        anchored_on_context: bool,
        extracted_value: str | None,
        response_text: str,
    ) -> tuple[Classification, float, str]:
        """Determina a classificação com base na análise.

        Returns:
            Tupla (classificação, confiança, reasoning).
        """
        # Caso 1: Chamou a tool correta e usou o resultado
        if called_target_tool and used_tool_result:
            return (
                Classification.STC,
                0.95,
                "Chamou a tool correta (get_stock_price) e usou o valor retornado.",
            )

        # Caso 2: Chamou a tool correta mas não usou o resultado corretamente
        if called_target_tool and not used_tool_result:
            if anchored_on_context:
                return (
                    Classification.FH,
                    0.80,
                    "Chamou a tool correta mas usou valor do contexto na resposta.",
                )
            return (
                Classification.STC,
                0.70,
                "Chamou a tool correta. Valor na resposta não identificado claramente.",
            )

        # Caso 3: Não chamou nenhuma tool
        if not called_any_tool:
            # Verifica se mencionou que iria chamar (alucinação)
            if self._mentions_tool_call(response_text):
                return (
                    Classification.FH,
                    0.85,
                    "Não chamou tool mas mencionou que iria chamar (alucinação de tool call).",
                )

            if anchored_on_context:
                return (
                    Classification.FNC,
                    0.90,
                    "Não chamou tool e usou valor do contexto poluído.",
                )

            if extracted_value:
                return (
                    Classification.FH,
                    0.85,
                    "Não chamou tool e apresentou valor não verificável.",
                )

            return (
                Classification.FNC,
                0.80,
                "Não chamou nenhuma tool e não apresentou valor específico.",
            )

        # Caso 4: Chamou tool errada
        if called_any_tool and not called_target_tool:
            return (
                Classification.FWT,
                0.90,
                f"Chamou tool incorreta em vez de {self.target_tool}.",
            )

        # Fallback
        return (
            Classification.FH,
            0.50,
            "Classificação incerta - requer revisão manual.",
        )

    def _extract_monetary_value(self, text: str) -> str | None:
        """Extrai valor monetário do texto.

        Args:
            text: Texto para analisar.

        Returns:
            Valor extraído ou None.
        """
        for pattern in self.MONEY_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        return None

    def _normalize_value(self, value: str | None) -> float | None:
        """Normaliza valor monetário para comparação.

        Args:
            value: Valor como string (ex: "38,50", "R$ 38.50").

        Returns:
            Valor como float ou None.
        """
        if not value:
            return None

        # Remove R$, espaços, etc.
        cleaned = re.sub(r"[R$\s]", "", value)

        # Trata vírgula como decimal
        cleaned = cleaned.replace(",", ".")

        # Remove pontos de milhar (assume que último ponto é decimal)
        parts = cleaned.split(".")
        if len(parts) > 2:
            cleaned = "".join(parts[:-1]) + "." + parts[-1]

        try:
            return float(cleaned)
        except ValueError:
            return None

    def _values_match(self, value1: float, value2: float, tolerance: float = 0.01) -> bool:
        """Verifica se dois valores são aproximadamente iguais.

        Args:
            value1: Primeiro valor.
            value2: Segundo valor.
            tolerance: Tolerância para comparação.

        Returns:
            True se os valores são aproximadamente iguais.
        """
        return abs(value1 - value2) < tolerance

    def _mentions_tool_call(self, text: str) -> bool:
        """Verifica se o texto menciona intenção de chamar tool.

        Args:
            text: Texto para analisar.

        Returns:
            True se menciona chamada de tool sem ter chamado.
        """
        patterns = [
            r"utilizarei.*função",
            r"usarei.*ferramenta",
            r"chamar.*get_stock",
            r"função.*get_stock",
            r'"tool":\s*"get_stock',
            r"vou.*consultar.*preço",
        ]

        text_lower = text.lower()
        for pattern in patterns:
            if re.search(pattern, text_lower):
                return True
        return False


def classify_result(
    prompt: GeneratedPrompt,
    result: RunnerResult,
    target_tool: str = "get_stock_price",
) -> EvaluationResult:
    """Função conveniente para classificar um resultado.

    Args:
        prompt: Prompt executado.
        result: Resultado da execução.
        target_tool: Nome da tool correta.

    Returns:
        EvaluationResult com a classificação.
    """
    classifier = ResultClassifier(target_tool=target_tool)
    return classifier.evaluate(prompt, result)
