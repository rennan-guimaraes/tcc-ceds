"""Testes para o runner de modelos."""

import pytest

from tcc_experiment.prompt import create_generator
from tcc_experiment.runner import OllamaRunner, RunnerResult, ToolCallResult


class TestToolCallResult:
    """Testes para ToolCallResult."""

    def test_create_basic(self) -> None:
        """Deve criar resultado básico."""
        result = ToolCallResult(tool_name="get_stock_price")
        assert result.tool_name == "get_stock_price"
        assert result.arguments is None
        assert result.result is None
        assert result.sequence_order == 1

    def test_create_with_all_fields(self) -> None:
        """Deve criar resultado com todos os campos."""
        result = ToolCallResult(
            tool_name="get_stock_price",
            arguments={"ticker": "PETR4"},
            result={"price": 38.50},
            sequence_order=2,
        )
        assert result.arguments == {"ticker": "PETR4"}
        assert result.result == {"price": 38.50}
        assert result.sequence_order == 2


class TestRunnerResult:
    """Testes para RunnerResult."""

    def test_success_result(self) -> None:
        """Deve criar resultado de sucesso."""
        result = RunnerResult(
            success=True,
            response_text="O preço atual é R$ 38,50",
            tool_calls=[
                ToolCallResult(tool_name="get_stock_price"),
            ],
        )
        assert result.success is True
        assert result.called_any_tool is True
        assert "get_stock_price" in result.called_tools_names

    def test_failure_result(self) -> None:
        """Deve criar resultado de falha."""
        result = RunnerResult(
            success=False,
            error="Connection timeout",
        )
        assert result.success is False
        assert result.error is not None
        assert result.called_any_tool is False

    def test_no_tool_calls(self) -> None:
        """Deve identificar quando não há tool calls."""
        result = RunnerResult(
            success=True,
            response_text="Baseado no relatório, o preço é R$ 35,00",
        )
        assert result.called_any_tool is False
        assert result.called_tools_names == []

    def test_multiple_tool_calls(self) -> None:
        """Deve listar múltiplas tool calls."""
        result = RunnerResult(
            success=True,
            response_text="Resposta",
            tool_calls=[
                ToolCallResult(tool_name="get_stock_price", sequence_order=1),
                ToolCallResult(tool_name="get_company_profile", sequence_order=2),
            ],
        )
        assert len(result.called_tools_names) == 2
        assert "get_stock_price" in result.called_tools_names
        assert "get_company_profile" in result.called_tools_names


class TestOllamaRunner:
    """Testes para OllamaRunner."""

    @pytest.fixture
    def runner(self) -> OllamaRunner:
        """Cria runner para testes."""
        return OllamaRunner()

    @pytest.fixture
    def sample_prompt(self):
        """Cria prompt de exemplo."""
        gen = create_generator()
        return gen.generate(0.0)

    def test_runner_initialization(self, runner: OllamaRunner) -> None:
        """Deve inicializar com valores padrão."""
        assert runner.host is not None
        assert runner.default_options["temperature"] == 0.0
        assert runner.default_options["seed"] == 42

    def test_runner_custom_host(self) -> None:
        """Deve aceitar host customizado."""
        runner = OllamaRunner(host="http://custom:11434")
        assert runner.host == "http://custom:11434"

    def test_runner_custom_temperature(self) -> None:
        """Deve aceitar temperatura customizada."""
        runner = OllamaRunner(temperature=0.7)
        assert runner.default_options["temperature"] == 0.7

    @pytest.mark.skipif(
        not OllamaRunner().is_available(),
        reason="Ollama não está disponível",
    )
    def test_list_models_when_available(self, runner: OllamaRunner) -> None:
        """Deve listar modelos quando Ollama está disponível."""
        models = runner.list_models()
        assert isinstance(models, list)

    def test_list_models_returns_list(self, runner: OllamaRunner) -> None:
        """list_models deve retornar lista (mesmo vazia)."""
        models = runner.list_models()
        assert isinstance(models, list)

    @pytest.mark.skipif(
        not OllamaRunner().is_available(),
        reason="Ollama não está disponível",
    )
    def test_is_available_true(self, runner: OllamaRunner) -> None:
        """Deve retornar True quando Ollama está acessível."""
        assert runner.is_available() is True

    @pytest.mark.skipif(
        not OllamaRunner().is_available(),
        reason="Ollama não está disponível",
    )
    def test_run_returns_runner_result(
        self, runner: OllamaRunner, sample_prompt
    ) -> None:
        """run deve retornar RunnerResult."""
        # Usa um modelo que provavelmente existe
        models = runner.list_models()
        if not models:
            pytest.skip("Nenhum modelo disponível")

        model = models[0]
        result = runner.run(sample_prompt, model=model)

        assert isinstance(result, RunnerResult)
        assert result.model_name == model
        assert result.latency_ms is not None
        assert result.latency_ms > 0


class TestOllamaRunnerMessageBuilding:
    """Testes para construção de mensagens."""

    @pytest.fixture
    def runner(self) -> OllamaRunner:
        return OllamaRunner()

    def test_build_messages_without_context(self, runner: OllamaRunner) -> None:
        """Deve construir mensagens sem contexto (pollution=0)."""
        gen = create_generator()
        prompt = gen.generate(0.0)

        messages = runner._build_messages(prompt)

        assert len(messages) == 2  # system + user
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
        assert "PETR4" in messages[1]["content"]

    def test_build_messages_with_context(self, runner: OllamaRunner) -> None:
        """Deve construir mensagens com contexto (pollution>0)."""
        gen = create_generator()
        prompt = gen.generate(40.0)

        messages = runner._build_messages(prompt)

        # system + context(user) + ack(assistant) + question(user)
        assert len(messages) == 4
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
        assert "CONTEXTO" in messages[1]["content"]
        assert messages[2]["role"] == "assistant"
        assert messages[3]["role"] == "user"
