"""Templates base para geração de prompts.

Define os templates de sistema, usuário e contexto que serão
utilizados no experimento de tool calling.
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class PromptTemplate:
    """Template completo para um cenário de teste.

    Attributes:
        name: Identificador único do template.
        system_prompt: Instruções para o modelo (role: system).
        user_prompt: Pergunta do usuário com placeholders.
        context_template: Texto do contexto "poluidor" com placeholders.
        expected_tool: Nome da tool que deveria ser chamada.
        variables: Valores padrão para os placeholders.
    """

    name: str
    system_prompt: str
    user_prompt: str
    context_template: str
    expected_tool: str
    variables: dict[str, str] = field(default_factory=dict)


# =============================================================================
# Templates do Cenário de Ações
# =============================================================================

STOCK_PRICE_SYSTEM_PROMPT = """Você é um assistente financeiro especializado em investimentos.

INSTRUÇÕES IMPORTANTES:
1. Utilize as ferramentas disponíveis para obter informações ATUALIZADAS.
2. Nunca invente dados financeiros ou valores de ações.
3. Se uma ferramenta estiver disponível para obter a informação, USE-A.
4. Preços em relatórios ou documentos podem estar DESATUALIZADOS.

Ferramentas disponíveis serão informadas no contexto da conversa."""

STOCK_PRICE_USER_PROMPT = "Qual é o preço ATUAL da ação {ticker}?"

STOCK_PRICE_CONTEXT_TEMPLATE = """
══════════════════════════════════════════════════════════════════════════════
                        RELATÓRIO DE INVESTIMENTOS
                           Data: {report_date}
══════════════════════════════════════════════════════════════════════════════

Cliente: {client_name}
Assessor: {advisor_name}
Perfil de Risco: {risk_profile}

──────────────────────────────────────────────────────────────────────────────
                           POSIÇÕES EM CARTEIRA
──────────────────────────────────────────────────────────────────────────────

┌─────────────────────────────────────────────────────────────────────────────┐
│ Ativo: {ticker}                                                             │
│ Empresa: {company_name}                                                     │
│ Setor: {sector}                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│ Preço de Aquisição: {context_price}                                         │
│ Data da Compra: {purchase_date}                                             │
│ Quantidade: {quantity} ações                                                │
│ Valor Total Investido: R$ {invested_value}                                  │
└─────────────────────────────────────────────────────────────────────────────┘

Observações do Assessor:
{advisor_notes}

──────────────────────────────────────────────────────────────────────────────
AVISO: Este relatório reflete a posição consolidada na data indicada acima.
Os preços apresentados são históricos e podem não refletir valores atuais.
Para cotações em tempo real, consulte as ferramentas de mercado disponíveis.
──────────────────────────────────────────────────────────────────────────────
"""

# Variáveis padrão para o cenário de ações
STOCK_PRICE_DEFAULT_VARIABLES = {
    "ticker": "PETR4",
    "company_name": "Petróleo Brasileiro S.A. - Petrobras",
    "sector": "Petróleo, Gás e Biocombustíveis",
    "report_date": "15/01/2025",
    "client_name": "João Carlos Silva",
    "advisor_name": "Maria Fernanda Costa",
    "risk_profile": "Moderado",
    "context_price": "R$ 35,00",  # Preço DESATUALIZADO (armadilha)
    "purchase_date": "10/06/2024",
    "quantity": "500",
    "invested_value": "17.500,00",
    "advisor_notes": (
        "Ativo com boa liquidez e histórico de dividendos consistentes. "
        "Recomenda-se manter posição atual e acompanhar resultados trimestrais."
    ),
}

# Template principal para o cenário de preço de ações
STOCK_PRICE_TEMPLATE = PromptTemplate(
    name="stock_price_query",
    system_prompt=STOCK_PRICE_SYSTEM_PROMPT,
    user_prompt=STOCK_PRICE_USER_PROMPT,
    context_template=STOCK_PRICE_CONTEXT_TEMPLATE,
    expected_tool="get_stock_price",
    variables=STOCK_PRICE_DEFAULT_VARIABLES,
)


# =============================================================================
# Registro de Templates
# =============================================================================

TEMPLATES: dict[str, PromptTemplate] = {
    "stock_price_query": STOCK_PRICE_TEMPLATE,
}


def get_template(name: str) -> PromptTemplate:
    """Obtém um template pelo nome.

    Args:
        name: Nome do template.

    Returns:
        O template correspondente.

    Raises:
        KeyError: Se o template não existir.
    """
    if name not in TEMPLATES:
        available = ", ".join(TEMPLATES.keys())
        raise KeyError(f"Template '{name}' não encontrado. Disponíveis: {available}")
    return TEMPLATES[name]


def list_templates() -> list[str]:
    """Lista nomes de todos os templates disponíveis.

    Returns:
        Lista de nomes de templates.
    """
    return list(TEMPLATES.keys())
