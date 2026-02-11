"""Modelos de dados para o experimento.

Define as estruturas de dados usando Pydantic para validação
e serialização automática.
"""

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class Classification(str, Enum):
    """Classificações possíveis para uma execução.

    Attributes:
        STC: Success-ToolCall - chamou a tool correta e usou o resultado.
        FNC: Fail-NoCall - não chamou nenhuma tool.
        FWT: Fail-WrongTool - chamou uma tool incorreta.
        FH: Fail-Hallucinated - inventou valor sem base.
    """

    STC = "STC"
    FNC = "FNC"
    FWT = "FWT"
    FH = "FH"

    @property
    def is_success(self) -> bool:
        """Retorna True se a classificação indica sucesso."""
        return self == Classification.STC

    @property
    def description(self) -> str:
        """Retorna descrição da classificação."""
        descriptions = {
            Classification.STC: "Chamou a tool correta e usou o resultado",
            Classification.FNC: "Não chamou nenhuma tool",
            Classification.FWT: "Chamou uma tool incorreta",
            Classification.FH: "Inventou valor sem base",
        }
        return descriptions[self]


class ExperimentStatus(str, Enum):
    """Status possíveis de um experimento."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Tool(BaseModel):
    """Definição de uma ferramenta (tool).

    Attributes:
        id: Identificador único.
        name: Nome da tool (ex: get_stock_price).
        description: Descrição para o LLM.
        parameters_schema: JSON Schema dos parâmetros.
        is_target: Se é a tool correta para o cenário.
    """

    id: UUID | None = None
    name: str
    description: str
    parameters_schema: dict[str, Any]
    is_target: bool = False
    mock_response: dict[str, Any] | None = None


class Model(BaseModel):
    """Modelo LLM para teste.

    Attributes:
        id: Identificador único.
        name: Nome do modelo (ex: qwen3).
        version: Versão (ex: 4b).
        provider: Provedor (ex: ollama).
        parameter_count: Quantidade de parâmetros (ex: 4B).
    """

    id: UUID | None = None
    name: str
    version: str | None = None
    provider: str = "ollama"
    parameter_count: str | None = None
    context_window: int | None = None


class Experiment(BaseModel):
    """Experimento completo.

    Attributes:
        id: Identificador único.
        name: Nome do experimento.
        description: Descrição detalhada.
        status: Status atual.
        pollution_levels: Níveis de poluição a testar.
        iterations_per_condition: Iterações por combinação.
    """

    id: UUID | None = None
    name: str
    description: str | None = None
    hypothesis: str | None = None
    status: ExperimentStatus = ExperimentStatus.PENDING
    pollution_levels: list[float] = Field(default=[0.0, 20.0, 40.0, 60.0])
    iterations_per_condition: int = Field(default=20, ge=1)
    created_at: datetime | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None


class ToolCall(BaseModel):
    """Chamada de tool feita pelo modelo.

    Attributes:
        tool_name: Nome da tool chamada.
        arguments: Argumentos passados.
        result: Resultado da execução.
        sequence_order: Ordem na sequência de chamadas.
    """

    tool_name: str
    arguments: dict[str, Any] | None = None
    result: dict[str, Any] | None = None
    error: str | None = None
    sequence_order: int = 1


class Execution(BaseModel):
    """Uma execução individual do experimento.

    Attributes:
        id: Identificador único.
        experiment_id: ID do experimento pai.
        model: Modelo utilizado.
        pollution_level: Nível de poluição aplicado.
        iteration_number: Número da iteração.
        tool_calls: Chamadas de tools feitas.
        classification: Classificação do resultado.
    """

    id: UUID | None = None
    experiment_id: UUID | None = None
    model: Model
    pollution_level: float = Field(ge=0.0, le=100.0)
    iteration_number: int = Field(ge=1)

    # Prompt
    system_prompt: str
    user_prompt: str
    context_content: str | None = None

    # Response
    raw_response: dict[str, Any] | None = None
    response_text: str | None = None
    tool_calls: list[ToolCall] = Field(default_factory=list)

    # Metrics
    latency_ms: int | None = None
    total_input_tokens: int | None = None
    response_tokens: int | None = None

    # Evaluation
    classification: Classification | None = None
    expected_value: str | None = None
    context_value: str | None = None
    extracted_value: str | None = None

    created_at: datetime | None = None
