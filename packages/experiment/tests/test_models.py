"""Testes para os modelos de dados."""

import pytest

from tcc_experiment.database.models import (
    Classification,
    Execution,
    Experiment,
    ExperimentStatus,
    Model,
    Tool,
)


class TestClassification:
    """Testes para a enum Classification."""

    def test_stc_is_success(self) -> None:
        """STC deve ser classificado como sucesso."""
        assert Classification.STC.is_success is True

    def test_failures_are_not_success(self) -> None:
        """FNC, FWT e FH não devem ser sucesso."""
        assert Classification.FNC.is_success is False
        assert Classification.FWT.is_success is False
        assert Classification.FH.is_success is False

    def test_all_have_descriptions(
        self, all_classifications: list[Classification]
    ) -> None:
        """Todas as classificações devem ter descrição."""
        for classification in all_classifications:
            assert classification.description
            assert len(classification.description) > 10


class TestModel:
    """Testes para o modelo Model."""

    def test_create_basic_model(self) -> None:
        """Deve criar modelo com campos básicos."""
        model = Model(name="test", provider="ollama")
        assert model.name == "test"
        assert model.provider == "ollama"
        assert model.id is None

    def test_model_with_all_fields(self, sample_model: Model) -> None:
        """Deve criar modelo com todos os campos."""
        assert sample_model.name == "qwen3"
        assert sample_model.version == "4b"
        assert sample_model.parameter_count == "4B"
        assert sample_model.context_window == 32768


class TestTool:
    """Testes para o modelo Tool."""

    def test_create_target_tool(self, sample_tools: list[Tool]) -> None:
        """Deve identificar tool alvo corretamente."""
        target = next(t for t in sample_tools if t.is_target)
        assert target.name == "get_stock_price"
        assert target.mock_response is not None

    def test_non_target_tool(self, sample_tools: list[Tool]) -> None:
        """Tools não-alvo não devem ter mock_response por padrão."""
        non_target = next(t for t in sample_tools if not t.is_target)
        assert non_target.name == "get_company_profile"


class TestExperiment:
    """Testes para o modelo Experiment."""

    def test_default_values(self) -> None:
        """Deve ter valores padrão corretos."""
        exp = Experiment(name="Test Experiment")
        assert exp.status == ExperimentStatus.PENDING
        assert exp.pollution_levels == [0.0, 20.0, 40.0, 60.0]
        assert exp.iterations_per_condition == 20

    def test_custom_pollution_levels(self) -> None:
        """Deve aceitar níveis de poluição customizados."""
        exp = Experiment(
            name="Custom",
            pollution_levels=[0.0, 25.0, 50.0, 75.0, 100.0],
        )
        assert len(exp.pollution_levels) == 5


class TestExecution:
    """Testes para o modelo Execution."""

    def test_pollution_level_validation(self, sample_model: Model) -> None:
        """Nível de poluição deve estar entre 0 e 100."""
        # Válido
        execution = Execution(
            model=sample_model,
            pollution_level=50.0,
            iteration_number=1,
            system_prompt="test",
            user_prompt="test",
        )
        assert execution.pollution_level == 50.0

    def test_invalid_pollution_level(self, sample_model: Model) -> None:
        """Deve rejeitar nível de poluição inválido."""
        with pytest.raises(ValueError):
            Execution(
                model=sample_model,
                pollution_level=150.0,  # Inválido
                iteration_number=1,
                system_prompt="test",
                user_prompt="test",
            )

    def test_tool_calls_default_empty(self, sample_model: Model) -> None:
        """Lista de tool calls deve ser vazia por padrão."""
        execution = Execution(
            model=sample_model,
            pollution_level=0.0,
            iteration_number=1,
            system_prompt="test",
            user_prompt="test",
        )
        assert execution.tool_calls == []
