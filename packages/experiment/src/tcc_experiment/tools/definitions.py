"""Definições das tools para o experimento.

Define as ferramentas disponíveis para os modelos LLM no formato
esperado pelo Ollama e outros provedores.
"""

from typing import Any

# =============================================================================
# Definições das Tools no formato Ollama
# =============================================================================

TOOL_GET_STOCK_PRICE: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "get_stock_price",
        "description": "Obtém o preço atual de uma ação pelo seu ticker/símbolo. Use esta ferramenta para consultar cotações em tempo real.",
        "parameters": {
            "type": "object",
            "properties": {
                "ticker": {
                    "type": "string",
                    "description": "O símbolo/ticker da ação (ex: PETR4, VALE3, AAPL)",
                }
            },
            "required": ["ticker"],
        },
    },
}

TOOL_GET_COMPANY_PROFILE: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "get_company_profile",
        "description": "Obtém informações detalhadas sobre uma empresa (setor, descrição, data de fundação, número de funcionários).",
        "parameters": {
            "type": "object",
            "properties": {
                "ticker": {
                    "type": "string",
                    "description": "O símbolo/ticker da ação",
                }
            },
            "required": ["ticker"],
        },
    },
}

TOOL_GET_PORTFOLIO_POSITIONS: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "get_portfolio_positions",
        "description": "Lista todas as posições de um cliente em sua carteira de investimentos.",
        "parameters": {
            "type": "object",
            "properties": {
                "client_id": {
                    "type": "string",
                    "description": "O identificador único do cliente",
                }
            },
            "required": ["client_id"],
        },
    },
}

TOOL_GET_FX_RATE: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "get_fx_rate",
        "description": "Obtém a taxa de câmbio atual entre duas moedas.",
        "parameters": {
            "type": "object",
            "properties": {
                "from_currency": {
                    "type": "string",
                    "description": "Moeda de origem (ex: USD, EUR, BRL)",
                },
                "to_currency": {
                    "type": "string",
                    "description": "Moeda de destino (ex: USD, EUR, BRL)",
                },
            },
            "required": ["from_currency", "to_currency"],
        },
    },
}

# Lista de todas as tools disponíveis
ALL_TOOLS: list[dict[str, Any]] = [
    TOOL_GET_STOCK_PRICE,
    TOOL_GET_COMPANY_PROFILE,
    TOOL_GET_PORTFOLIO_POSITIONS,
    TOOL_GET_FX_RATE,
]

# Mapeamento de nome para definição
TOOLS_BY_NAME: dict[str, dict[str, Any]] = {
    "get_stock_price": TOOL_GET_STOCK_PRICE,
    "get_company_profile": TOOL_GET_COMPANY_PROFILE,
    "get_portfolio_positions": TOOL_GET_PORTFOLIO_POSITIONS,
    "get_fx_rate": TOOL_GET_FX_RATE,
}


# =============================================================================
# Respostas Mock das Tools (para experimento controlado)
# =============================================================================

MOCK_RESPONSES: dict[str, dict[str, Any]] = {
    "get_stock_price": {
        "PETR4": {"ticker": "PETR4", "price": 38.50, "currency": "BRL", "change": "+1.2%"},
        "VALE3": {"ticker": "VALE3", "price": 67.80, "currency": "BRL", "change": "-0.5%"},
        "AAPL": {"ticker": "AAPL", "price": 185.50, "currency": "USD", "change": "+0.8%"},
        "DEFAULT": {"ticker": "UNKNOWN", "price": 0.0, "currency": "BRL", "error": "Ticker não encontrado"},
    },
    "get_company_profile": {
        "PETR4": {
            "ticker": "PETR4",
            "name": "Petróleo Brasileiro S.A. - Petrobras",
            "sector": "Petróleo, Gás e Biocombustíveis",
            "founded": "1953",
        },
        "DEFAULT": {"error": "Empresa não encontrada"},
    },
    "get_portfolio_positions": {
        "DEFAULT": {"error": "Cliente não encontrado"},
    },
    "get_fx_rate": {
        "USD/BRL": {"pair": "USD/BRL", "rate": 4.95, "timestamp": "2025-01-29T10:00:00Z"},
        "EUR/BRL": {"pair": "EUR/BRL", "rate": 5.35, "timestamp": "2025-01-29T10:00:00Z"},
        "DEFAULT": {"error": "Par de moedas não suportado"},
    },
}


def get_mock_response(tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """Retorna resposta mock para uma tool.

    Args:
        tool_name: Nome da tool.
        arguments: Argumentos passados para a tool.

    Returns:
        Resposta mock da tool.
    """
    if tool_name not in MOCK_RESPONSES:
        return {"error": f"Tool '{tool_name}' não encontrada"}

    tool_mocks = MOCK_RESPONSES[tool_name]

    # Tenta encontrar resposta específica baseada nos argumentos
    if tool_name == "get_stock_price":
        ticker = arguments.get("ticker", "").upper()
        return tool_mocks.get(ticker, tool_mocks["DEFAULT"])

    elif tool_name == "get_company_profile":
        ticker = arguments.get("ticker", "").upper()
        return tool_mocks.get(ticker, tool_mocks["DEFAULT"])

    elif tool_name == "get_fx_rate":
        from_curr = arguments.get("from_currency", "").upper()
        to_curr = arguments.get("to_currency", "").upper()
        pair = f"{from_curr}/{to_curr}"
        return tool_mocks.get(pair, tool_mocks["DEFAULT"])

    return tool_mocks.get("DEFAULT", {"error": "Resposta não disponível"})


def get_tools_for_experiment() -> list[dict[str, Any]]:
    """Retorna lista de tools para o experimento.

    Returns:
        Lista de definições de tools no formato Ollama.
    """
    return ALL_TOOLS.copy()
