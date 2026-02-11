"""Testes para as definições de tools."""


from tcc_experiment.tools import (
    ALL_TOOLS,
    TOOLS_BY_NAME,
    get_mock_response,
    get_tools_for_experiment,
)


class TestToolDefinitions:
    """Testes para as definições de tools."""

    def test_all_tools_has_four_tools(self) -> None:
        """Deve haver exatamente 4 tools definidas."""
        assert len(ALL_TOOLS) == 4

    def test_tools_have_correct_format(self) -> None:
        """Todas as tools devem ter o formato correto para Ollama."""
        for tool in ALL_TOOLS:
            assert tool["type"] == "function"
            assert "function" in tool
            assert "name" in tool["function"]
            assert "description" in tool["function"]
            assert "parameters" in tool["function"]

    def test_get_stock_price_is_defined(self) -> None:
        """get_stock_price deve estar definida."""
        assert "get_stock_price" in TOOLS_BY_NAME
        tool = TOOLS_BY_NAME["get_stock_price"]
        assert tool["function"]["name"] == "get_stock_price"

    def test_get_tools_for_experiment_returns_copy(self) -> None:
        """get_tools_for_experiment deve retornar uma cópia."""
        tools1 = get_tools_for_experiment()
        tools2 = get_tools_for_experiment()
        assert tools1 is not tools2
        assert tools1 == tools2


class TestMockResponses:
    """Testes para as respostas mock das tools."""

    def test_get_stock_price_petr4(self) -> None:
        """Deve retornar preço correto para PETR4."""
        result = get_mock_response("get_stock_price", {"ticker": "PETR4"})
        assert result["ticker"] == "PETR4"
        assert result["price"] == 38.50
        assert result["currency"] == "BRL"

    def test_get_stock_price_unknown_ticker(self) -> None:
        """Deve retornar erro para ticker desconhecido."""
        result = get_mock_response("get_stock_price", {"ticker": "XYZW11"})
        assert "error" in result

    def test_get_stock_price_case_insensitive(self) -> None:
        """Deve funcionar com ticker em minúsculas."""
        result = get_mock_response("get_stock_price", {"ticker": "petr4"})
        assert result["ticker"] == "PETR4"

    def test_get_company_profile_petr4(self) -> None:
        """Deve retornar perfil da Petrobras."""
        result = get_mock_response("get_company_profile", {"ticker": "PETR4"})
        assert "Petrobras" in result["name"]
        assert result["sector"] is not None

    def test_get_fx_rate_usd_brl(self) -> None:
        """Deve retornar taxa USD/BRL."""
        result = get_mock_response(
            "get_fx_rate",
            {"from_currency": "USD", "to_currency": "BRL"},
        )
        assert result["pair"] == "USD/BRL"
        assert result["rate"] > 0

    def test_unknown_tool(self) -> None:
        """Deve retornar erro para tool desconhecida."""
        result = get_mock_response("unknown_tool", {})
        assert "error" in result
