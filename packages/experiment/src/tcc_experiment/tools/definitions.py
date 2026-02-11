"""Definições das tools para o experimento.

Define as ferramentas disponíveis para os modelos LLM no formato
esperado pelo Ollama e outros provedores.
"""

from enum import Enum
from typing import Any


class ToolSet(str, Enum):
    """Conjunto de tools disponíveis para o experimento.

    Values:
        BASE: 4 tools originais (1 correta + 3 pegadinhas).
        EXPANDED: 8 tools (1 correta + 7 pegadinhas).
    """

    BASE = "base"
    EXPANDED = "expanded"

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

# --- Tools expandidas (pegadinhas adicionais) ---

TOOL_GET_STOCK_DIVIDEND_HISTORY: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "get_stock_dividend_history",
        "description": "Obtém o histórico de dividendos pagos por uma ação.",
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

TOOL_GET_ANALYST_RATING: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "get_analyst_rating",
        "description": "Obtém a recomendação e nota dos analistas para uma ação.",
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

TOOL_GET_MARKET_NEWS: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "get_market_news",
        "description": "Busca as últimas notícias do mercado sobre uma ação.",
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

TOOL_GET_CURRENT_DATETIME: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "get_current_datetime",
        "description": "Retorna a data e hora atuais do sistema.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
}

# =============================================================================
# Conjuntos de Tools
# =============================================================================

BASE_TOOLS: list[dict[str, Any]] = [
    TOOL_GET_STOCK_PRICE,
    TOOL_GET_COMPANY_PROFILE,
    TOOL_GET_PORTFOLIO_POSITIONS,
    TOOL_GET_FX_RATE,
]

EXPANDED_TOOLS: list[dict[str, Any]] = BASE_TOOLS + [
    TOOL_GET_STOCK_DIVIDEND_HISTORY,
    TOOL_GET_ANALYST_RATING,
    TOOL_GET_MARKET_NEWS,
    TOOL_GET_CURRENT_DATETIME,
]

# Backward compatibility
ALL_TOOLS: list[dict[str, Any]] = BASE_TOOLS

# Mapeamento de nome para definição
TOOLS_BY_NAME: dict[str, dict[str, Any]] = {
    "get_stock_price": TOOL_GET_STOCK_PRICE,
    "get_company_profile": TOOL_GET_COMPANY_PROFILE,
    "get_portfolio_positions": TOOL_GET_PORTFOLIO_POSITIONS,
    "get_fx_rate": TOOL_GET_FX_RATE,
    "get_stock_dividend_history": TOOL_GET_STOCK_DIVIDEND_HISTORY,
    "get_analyst_rating": TOOL_GET_ANALYST_RATING,
    "get_market_news": TOOL_GET_MARKET_NEWS,
    "get_current_datetime": TOOL_GET_CURRENT_DATETIME,
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
    "get_stock_dividend_history": {
        "PETR4": {
            "ticker": "PETR4",
            "dividends": [
                {"date": "2024-12-15", "type": "JCP", "value_per_share": 1.25},
                {"date": "2024-08-20", "type": "Dividendo", "value_per_share": 0.85},
                {"date": "2024-05-10", "type": "JCP", "value_per_share": 1.10},
            ],
        },
        "DEFAULT": {"error": "Ticker não encontrado"},
    },
    "get_analyst_rating": {
        "PETR4": {
            "ticker": "PETR4",
            "consensus": "Compra",
            "target_price": 42.00,
            "total_analysts": 12,
            "buy": 8,
            "hold": 3,
            "sell": 1,
        },
        "DEFAULT": {"error": "Ticker não encontrado"},
    },
    "get_market_news": {
        "PETR4": {
            "ticker": "PETR4",
            "news": [
                {"title": "Petrobras anuncia novo plano de investimentos", "date": "2025-02-03", "source": "InfoMoney"},
                {"title": "Produção de petróleo atinge recorde no 4T24", "date": "2025-01-28", "source": "Valor Econômico"},
            ],
        },
        "DEFAULT": {"error": "Ticker não encontrado"},
    },
    "get_current_datetime": {
        "DEFAULT": {"datetime": "2025-02-04T14:35:00-03:00", "timezone": "America/Sao_Paulo"},
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

    # Tools que usam ticker como chave
    if tool_name in (
        "get_stock_price",
        "get_company_profile",
        "get_stock_dividend_history",
        "get_analyst_rating",
        "get_market_news",
    ):
        ticker = arguments.get("ticker", "").upper()
        return tool_mocks.get(ticker, tool_mocks["DEFAULT"])

    if tool_name == "get_fx_rate":
        from_curr = arguments.get("from_currency", "").upper()
        to_curr = arguments.get("to_currency", "").upper()
        pair = f"{from_curr}/{to_curr}"
        return tool_mocks.get(pair, tool_mocks["DEFAULT"])

    # Tools sem argumentos (get_current_datetime) ou fallback
    return tool_mocks.get("DEFAULT", {"error": "Resposta não disponível"})


def get_tools_for_experiment(tool_set: ToolSet = ToolSet.BASE) -> list[dict[str, Any]]:
    """Retorna lista de tools para o experimento.

    Args:
        tool_set: Conjunto de tools a usar (base=4, expanded=8).

    Returns:
        Lista de definições de tools no formato Ollama.
    """
    if tool_set == ToolSet.EXPANDED:
        return EXPANDED_TOOLS.copy()
    return BASE_TOOLS.copy()
