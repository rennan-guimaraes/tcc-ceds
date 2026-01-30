"""Interface base para runners de modelos LLM.

Define o contrato que todas as implementações de runner devem seguir.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from tcc_experiment.prompt.generator import GeneratedPrompt


@dataclass
class ToolCallResult:
    """Resultado de uma chamada de tool.

    Attributes:
        tool_name: Nome da tool chamada.
        arguments: Argumentos passados.
        result: Resultado da execução.
        error: Mensagem de erro, se houver.
        sequence_order: Ordem na sequência de chamadas.
    """

    tool_name: str
    arguments: dict[str, Any] | None = None
    result: dict[str, Any] | None = None
    error: str | None = None
    sequence_order: int = 1


@dataclass
class RunnerResult:
    """Resultado da execução de um prompt.

    Attributes:
        success: Se a execução foi bem-sucedida.
        response_text: Texto da resposta final do modelo.
        tool_calls: Lista de chamadas de tools feitas.
        raw_response: Resposta bruta da API.
        latency_ms: Tempo de execução em milissegundos.
        input_tokens: Número de tokens de entrada (estimado).
        output_tokens: Número de tokens de saída (estimado).
        model_name: Nome do modelo usado.
        error: Mensagem de erro, se houver.
    """

    success: bool
    response_text: str | None = None
    tool_calls: list[ToolCallResult] = field(default_factory=list)
    raw_response: dict[str, Any] | None = None
    latency_ms: int | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    model_name: str | None = None
    error: str | None = None

    @property
    def called_any_tool(self) -> bool:
        """Retorna True se alguma tool foi chamada."""
        return len(self.tool_calls) > 0

    @property
    def called_tools_names(self) -> list[str]:
        """Retorna lista de nomes das tools chamadas."""
        return [tc.tool_name for tc in self.tool_calls]


class BaseRunner(ABC):
    """Interface abstrata para runners de modelos LLM.

    Runners são responsáveis por executar prompts em modelos LLM
    e retornar os resultados de forma padronizada.
    """

    @abstractmethod
    def run(
        self,
        prompt: GeneratedPrompt,
        model: str,
        tools: list[dict[str, Any]] | None = None,
    ) -> RunnerResult:
        """Executa um prompt no modelo.

        Args:
            prompt: Prompt gerado a ser executado.
            model: Nome/identificador do modelo.
            tools: Lista de tools disponíveis (formato Ollama).

        Returns:
            RunnerResult com os resultados da execução.
        """
        pass

    @abstractmethod
    def list_models(self) -> list[str]:
        """Lista modelos disponíveis.

        Returns:
            Lista de nomes de modelos.
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Verifica se o runner está disponível.

        Returns:
            True se o runner pode ser usado.
        """
        pass
