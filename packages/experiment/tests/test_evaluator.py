"""Testes para o classificador de resultados."""

import pytest

from tcc_experiment.database.models import Classification
from tcc_experiment.evaluator import EvaluationResult, ResultClassifier, classify_result
from tcc_experiment.prompt import create_generator
from tcc_experiment.runner import RunnerResult, ToolCallResult


class TestResultClassifier:
    """Testes para o classificador de resultados."""

    @pytest.fixture
    def classifier(self) -> ResultClassifier:
        """Cria classificador para testes."""
        return ResultClassifier(target_tool="get_stock_price")

    @pytest.fixture
    def prompt_0_pollution(self):
        """Prompt sem poluição."""
        gen = create_generator()
        return gen.generate(0.0)

    @pytest.fixture
    def prompt_40_pollution(self):
        """Prompt com 40% de poluição."""
        gen = create_generator()
        return gen.generate(40.0)

    # =========================================================================
    # Testes de Classificação STC (Success-ToolCall)
    # =========================================================================

    def test_stc_called_correct_tool_used_result(
        self, classifier: ResultClassifier, prompt_0_pollution
    ) -> None:
        """STC: Chamou tool correta e usou o resultado."""
        result = RunnerResult(
            success=True,
            response_text="O preço atual da PETR4 é R$ 38,50.",
            tool_calls=[
                ToolCallResult(
                    tool_name="get_stock_price",
                    arguments={"ticker": "PETR4"},
                    result={"price": 38.50},
                )
            ],
        )

        evaluation = classifier.evaluate(prompt_0_pollution, result)

        assert evaluation.classification == Classification.STC
        assert evaluation.called_target_tool is True
        assert evaluation.used_tool_result is True
        assert evaluation.confidence_score >= 0.9

    def test_stc_with_different_format(
        self, classifier: ResultClassifier, prompt_0_pollution
    ) -> None:
        """STC: Valor em formato diferente mas correto."""
        result = RunnerResult(
            success=True,
            response_text="A cotação atual é 38.50 BRL.",
            tool_calls=[
                ToolCallResult(tool_name="get_stock_price"),
            ],
        )

        evaluation = classifier.evaluate(prompt_0_pollution, result)

        assert evaluation.classification == Classification.STC
        assert evaluation.extracted_value is not None

    # =========================================================================
    # Testes de Classificação FNC (Fail-NoCall)
    # =========================================================================

    def test_fnc_no_tool_used_context_value(
        self, classifier: ResultClassifier, prompt_40_pollution
    ) -> None:
        """FNC: Não chamou tool e usou valor do contexto."""
        result = RunnerResult(
            success=True,
            response_text="Conforme o relatório, o preço da PETR4 é R$ 35,00.",
            tool_calls=[],
        )

        evaluation = classifier.evaluate(prompt_40_pollution, result)

        assert evaluation.classification == Classification.FNC
        assert evaluation.called_any_tool is False
        assert evaluation.anchored_on_context is True

    def test_fnc_no_tool_no_value(
        self, classifier: ResultClassifier, prompt_0_pollution
    ) -> None:
        """FNC: Não chamou tool e não deu valor específico."""
        result = RunnerResult(
            success=True,
            response_text="Não tenho informações sobre o preço atual.",
            tool_calls=[],
        )

        evaluation = classifier.evaluate(prompt_0_pollution, result)

        assert evaluation.classification == Classification.FNC
        assert evaluation.called_any_tool is False

    # =========================================================================
    # Testes de Classificação FWT (Fail-WrongTool)
    # =========================================================================

    def test_fwt_called_wrong_tool(
        self, classifier: ResultClassifier, prompt_0_pollution
    ) -> None:
        """FWT: Chamou tool errada."""
        result = RunnerResult(
            success=True,
            response_text="Obtive informações da empresa.",
            tool_calls=[
                ToolCallResult(
                    tool_name="get_company_profile",
                    arguments={"ticker": "PETR4"},
                )
            ],
        )

        evaluation = classifier.evaluate(prompt_0_pollution, result)

        assert evaluation.classification == Classification.FWT
        assert evaluation.called_any_tool is True
        assert evaluation.called_target_tool is False

    # =========================================================================
    # Testes de Classificação FH (Fail-Hallucinated)
    # =========================================================================

    def test_fh_mentioned_tool_but_didnt_call(
        self, classifier: ResultClassifier, prompt_0_pollution
    ) -> None:
        """FH: Mencionou que iria chamar tool mas não chamou."""
        result = RunnerResult(
            success=True,
            response_text='Vou utilizar a função get_stock_price para obter o preço. {"tool": "get_stock_price"}',
            tool_calls=[],
        )

        evaluation = classifier.evaluate(prompt_0_pollution, result)

        assert evaluation.classification == Classification.FH
        assert evaluation.called_any_tool is False

    def test_fh_invented_value(
        self, classifier: ResultClassifier, prompt_0_pollution
    ) -> None:
        """FH: Inventou valor sem chamar tool."""
        result = RunnerResult(
            success=True,
            response_text="O preço atual da PETR4 é R$ 42,00.",
            tool_calls=[],
        )

        evaluation = classifier.evaluate(prompt_0_pollution, result)

        # Valor não é do contexto nem da tool, então é FH
        assert evaluation.classification == Classification.FH
        assert evaluation.extracted_value == "42,00"


class TestValueExtraction:
    """Testes para extração de valores monetários."""

    @pytest.fixture
    def classifier(self) -> ResultClassifier:
        return ResultClassifier()

    def test_extract_br_format(self, classifier: ResultClassifier) -> None:
        """Extrai valor no formato brasileiro."""
        value = classifier._extract_monetary_value("O preço é R$ 38,50")
        assert value == "38,50"

    def test_extract_us_format(self, classifier: ResultClassifier) -> None:
        """Extrai valor no formato americano."""
        value = classifier._extract_monetary_value("Price is R$ 38.50")
        assert value == "38.50"

    def test_extract_with_brl(self, classifier: ResultClassifier) -> None:
        """Extrai valor com BRL."""
        value = classifier._extract_monetary_value("Cotação: 38,50 BRL")
        assert value == "38,50"

    def test_extract_no_value(self, classifier: ResultClassifier) -> None:
        """Retorna None quando não há valor."""
        value = classifier._extract_monetary_value("Não tenho informação")
        assert value is None


class TestValueNormalization:
    """Testes para normalização de valores."""

    @pytest.fixture
    def classifier(self) -> ResultClassifier:
        return ResultClassifier()

    def test_normalize_br_format(self, classifier: ResultClassifier) -> None:
        """Normaliza formato brasileiro."""
        assert classifier._normalize_value("38,50") == 38.50

    def test_normalize_us_format(self, classifier: ResultClassifier) -> None:
        """Normaliza formato americano."""
        assert classifier._normalize_value("38.50") == 38.50

    def test_normalize_with_currency(self, classifier: ResultClassifier) -> None:
        """Normaliza com símbolo de moeda."""
        assert classifier._normalize_value("R$ 38,50") == 38.50

    def test_normalize_none(self, classifier: ResultClassifier) -> None:
        """Retorna None para entrada None."""
        assert classifier._normalize_value(None) is None

    def test_values_match(self, classifier: ResultClassifier) -> None:
        """Verifica comparação de valores."""
        assert classifier._values_match(38.50, 38.50) is True
        assert classifier._values_match(38.50, 38.51) is True  # Dentro da tolerância
        assert classifier._values_match(38.50, 35.00) is False


class TestClassifyResultFunction:
    """Testes para a função classify_result."""

    def test_classify_result_convenience(self) -> None:
        """classify_result deve funcionar como atalho."""
        gen = create_generator()
        prompt = gen.generate(0.0)

        result = RunnerResult(
            success=True,
            response_text="Preço: R$ 38,50",
            tool_calls=[ToolCallResult(tool_name="get_stock_price")],
        )

        evaluation = classify_result(prompt, result)

        assert isinstance(evaluation, EvaluationResult)
        assert evaluation.classification == Classification.STC
