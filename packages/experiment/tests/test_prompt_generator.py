"""Testes para o gerador de prompts."""

import pytest

from tcc_experiment.prompt import (
    GeneratedPrompt,
    PromptGenerator,
    PromptTemplate,
    create_generator,
    get_template,
    list_templates,
)


class TestPromptTemplate:
    """Testes para templates de prompt."""

    def test_list_templates_not_empty(self) -> None:
        """Deve haver pelo menos um template disponível."""
        templates = list_templates()
        assert len(templates) > 0
        assert "stock_price_query" in templates

    def test_get_template_exists(self) -> None:
        """Deve retornar template existente."""
        template = get_template("stock_price_query")
        assert isinstance(template, PromptTemplate)
        assert template.name == "stock_price_query"
        assert template.expected_tool == "get_stock_price"

    def test_get_template_not_found(self) -> None:
        """Deve levantar erro para template inexistente."""
        with pytest.raises(KeyError, match="não encontrado"):
            get_template("nonexistent_template")

    def test_template_has_required_fields(self) -> None:
        """Template deve ter todos os campos obrigatórios."""
        template = get_template("stock_price_query")
        assert template.system_prompt
        assert template.user_prompt
        assert template.context_template
        assert template.expected_tool
        assert template.variables


class TestPromptGenerator:
    """Testes para o gerador de prompts."""

    @pytest.fixture
    def generator(self) -> PromptGenerator:
        """Cria um gerador padrão para testes."""
        return PromptGenerator()

    def test_generate_zero_pollution(self, generator: PromptGenerator) -> None:
        """Poluição 0% não deve incluir contexto."""
        prompt = generator.generate(0.0)

        assert prompt.pollution_level == 0.0
        assert prompt.context is None
        assert prompt.context_repetitions == 0
        assert "PETR4" in prompt.user_prompt

    def test_generate_with_pollution(self, generator: PromptGenerator) -> None:
        """Poluição > 0% deve incluir contexto."""
        prompt = generator.generate(20.0)

        assert prompt.pollution_level == 20.0
        assert prompt.context is not None
        assert prompt.context_repetitions == 1
        assert "RELATÓRIO" in prompt.context

    def test_pollution_increases_repetitions(self, generator: PromptGenerator) -> None:
        """Mais poluição deve gerar mais repetições."""
        prompt_20 = generator.generate(20.0)
        prompt_40 = generator.generate(40.0)
        prompt_60 = generator.generate(60.0)

        assert prompt_20.context_repetitions < prompt_40.context_repetitions
        assert prompt_40.context_repetitions < prompt_60.context_repetitions

    def test_context_contains_trap_value(self, generator: PromptGenerator) -> None:
        """Contexto deve conter o valor armadilha."""
        prompt = generator.generate(40.0)

        assert prompt.context_value == "R$ 35,00"
        assert "R$ 35,00" in prompt.context  # type: ignore

    def test_expected_value_differs_from_context(
        self, generator: PromptGenerator
    ) -> None:
        """Valor esperado deve ser diferente do valor no contexto."""
        prompt = generator.generate(40.0)

        assert prompt.expected_value != prompt.context_value

    def test_prompt_hash_is_consistent(self, generator: PromptGenerator) -> None:
        """Mesmo prompt deve gerar mesmo hash."""
        prompt1 = generator.generate(40.0)
        prompt2 = generator.generate(40.0)

        assert prompt1.prompt_hash == prompt2.prompt_hash

    def test_different_pollution_different_hash(
        self, generator: PromptGenerator
    ) -> None:
        """Níveis diferentes de poluição devem gerar hashes diferentes."""
        prompt1 = generator.generate(20.0)
        prompt2 = generator.generate(40.0)

        assert prompt1.prompt_hash != prompt2.prompt_hash

    def test_invalid_pollution_level_negative(
        self, generator: PromptGenerator
    ) -> None:
        """Deve rejeitar nível de poluição negativo."""
        with pytest.raises(ValueError, match="entre 0 e 100"):
            generator.generate(-10.0)

    def test_invalid_pollution_level_over_100(
        self, generator: PromptGenerator
    ) -> None:
        """Deve rejeitar nível de poluição acima de 100."""
        with pytest.raises(ValueError, match="entre 0 e 100"):
            generator.generate(150.0)

    def test_custom_variables(self) -> None:
        """Deve aceitar variáveis customizadas."""
        generator = PromptGenerator(
            variables_override={"ticker": "VALE3", "context_price": "R$ 60,00"}
        )
        prompt = generator.generate(20.0)

        assert "VALE3" in prompt.user_prompt
        assert "R$ 60,00" in prompt.context  # type: ignore

    def test_get_pollution_levels(self, generator: PromptGenerator) -> None:
        """Deve retornar níveis de poluição ordenados."""
        levels = generator.get_pollution_levels()

        assert 0.0 in levels
        assert 20.0 in levels
        assert 40.0 in levels
        assert 60.0 in levels
        assert levels == sorted(levels)

    def test_full_prompt_property(self, generator: PromptGenerator) -> None:
        """full_prompt deve concatenar todos os componentes."""
        prompt = generator.generate(40.0)
        full = prompt.full_prompt

        assert prompt.system_prompt in full
        assert prompt.user_prompt in full
        assert prompt.context in full  # type: ignore


class TestCreateGenerator:
    """Testes para a factory function."""

    def test_create_default_generator(self) -> None:
        """Deve criar gerador com valores padrão."""
        gen = create_generator()
        prompt = gen.generate(0.0)

        assert prompt.template_name == "stock_price_neutral"
        assert prompt.expected_tool == "get_stock_price"

    def test_create_with_custom_values(self) -> None:
        """Deve criar gerador com valores customizados."""
        gen = create_generator(
            ticker="MGLU3",
            context_price="R$ 5,00",
            expected_value="R$ 8,00",
        )
        prompt = gen.generate(20.0)

        assert "MGLU3" in prompt.user_prompt
        assert "R$ 5,00" in prompt.context  # type: ignore
        assert prompt.expected_value == "R$ 8,00"


class TestGeneratedPrompt:
    """Testes para a dataclass GeneratedPrompt."""

    def test_full_prompt_without_context(self) -> None:
        """full_prompt sem contexto deve ter apenas sistema e usuário."""
        prompt = GeneratedPrompt(
            system_prompt="Sistema",
            user_prompt="Usuário",
            context=None,
            pollution_level=0.0,
            template_name="test",
            expected_tool="test_tool",
            expected_value="expected",
            context_value="context",
            prompt_hash="abc123",
            context_repetitions=0,
        )

        full = prompt.full_prompt
        assert "Sistema" in full
        assert "Usuário" in full
        assert full.count("\n\n") == 1  # Apenas um separador

    def test_full_prompt_with_context(self) -> None:
        """full_prompt com contexto deve incluir todos os componentes."""
        prompt = GeneratedPrompt(
            system_prompt="Sistema",
            user_prompt="Usuário",
            context="Contexto",
            pollution_level=40.0,
            template_name="test",
            expected_tool="test_tool",
            expected_value="expected",
            context_value="context",
            prompt_hash="abc123",
            context_repetitions=3,
        )

        full = prompt.full_prompt
        assert "Sistema" in full
        assert "Contexto" in full
        assert "Usuário" in full
