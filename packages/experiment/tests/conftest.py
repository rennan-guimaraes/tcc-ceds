"""Fixtures compartilhadas para os testes."""

import pytest

from tcc_experiment.database.models import Classification, Model, Tool


@pytest.fixture
def sample_model() -> Model:
    """Retorna um modelo de exemplo para testes."""
    return Model(
        name="qwen3",
        version="4b",
        provider="ollama",
        parameter_count="4B",
        context_window=32768,
    )


@pytest.fixture
def sample_tools() -> list[Tool]:
    """Retorna lista de tools de exemplo para testes."""
    return [
        Tool(
            name="get_stock_price",
            description="Obtém o preço atual de uma ação.",
            parameters_schema={
                "type": "object",
                "properties": {
                    "ticker": {"type": "string", "description": "Símbolo da ação"},
                },
                "required": ["ticker"],
            },
            is_target=True,
            mock_response={"ticker": "PETR4", "price": 38.50, "currency": "BRL"},
        ),
        Tool(
            name="get_company_profile",
            description="Obtém informações sobre uma empresa.",
            parameters_schema={
                "type": "object",
                "properties": {
                    "ticker": {"type": "string"},
                },
                "required": ["ticker"],
            },
            is_target=False,
        ),
    ]


@pytest.fixture
def all_classifications() -> list[Classification]:
    """Retorna todas as classificações possíveis."""
    return list(Classification)
