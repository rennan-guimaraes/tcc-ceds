"""Runner para modelos Ollama.

Implementa a execução de prompts usando a API do Ollama,
com suporte a tool calling.
"""

import json
import time
from typing import Any

import ollama
from ollama import ResponseError

from tcc_experiment.config import get_settings
from tcc_experiment.prompt.generator import GeneratedPrompt
from tcc_experiment.runner.base import BaseRunner, RunnerResult, ToolCallResult
from tcc_experiment.tools.definitions import get_mock_response, get_tools_for_experiment


class OllamaRunner(BaseRunner):
    """Runner para modelos Ollama.

    Executa prompts em modelos locais via Ollama, com suporte
    completo a tool calling.

    Attributes:
        host: URL do servidor Ollama.
        default_options: Opções padrão para as chamadas.

    Example:
        >>> runner = OllamaRunner()
        >>> result = runner.run(prompt, model="qwen3:4b")
        >>> print(result.response_text)
    """

    def __init__(
        self,
        host: str | None = None,
        temperature: float = 0.0,
        seed: int = 42,
        num_ctx: int | None = None,
    ) -> None:
        """Inicializa o runner.

        Args:
            host: URL do servidor Ollama (usa config se None).
            temperature: Temperatura para geração (0 = determinístico).
            seed: Seed para reprodutibilidade.
            num_ctx: Tamanho da janela de contexto (usa config se None).
        """
        settings = get_settings()
        self.host = host or settings.ollama_host
        self.default_options = {
            "temperature": temperature,
            "seed": seed,
            "num_ctx": num_ctx or settings.ollama_num_ctx,
        }

        # Configura cliente Ollama
        self._client = ollama.Client(host=self.host)

    def run(
        self,
        prompt: GeneratedPrompt,
        model: str,
        tools: list[dict[str, Any]] | None = None,
    ) -> RunnerResult:
        """Executa um prompt no modelo Ollama.

        Args:
            prompt: Prompt gerado a ser executado.
            model: Nome do modelo (ex: qwen3:4b).
            tools: Lista de tools (usa padrão se None).

        Returns:
            RunnerResult com os resultados da execução.
        """
        if tools is None:
            tools = get_tools_for_experiment()

        # Monta mensagens
        messages = self._build_messages(prompt)

        # Executa com medição de tempo
        start_time = time.perf_counter()

        try:
            result = self._execute_with_tools(messages, model, tools)
            latency_ms = int((time.perf_counter() - start_time) * 1000)
            result.latency_ms = latency_ms
            result.model_name = model
            return result

        except ResponseError as e:
            latency_ms = int((time.perf_counter() - start_time) * 1000)
            return RunnerResult(
                success=False,
                error=f"Ollama error: {e}",
                latency_ms=latency_ms,
                model_name=model,
            )
        except Exception as e:
            latency_ms = int((time.perf_counter() - start_time) * 1000)
            return RunnerResult(
                success=False,
                error=f"Unexpected error: {type(e).__name__}: {e}",
                latency_ms=latency_ms,
                model_name=model,
            )

    def _build_messages(self, prompt: GeneratedPrompt) -> list[dict[str, str]]:
        """Constrói lista de mensagens para o Ollama.

        Contexto e pergunta vão na mesma mensagem do usuário,
        sem tags artificiais ou resposta sintética do assistant.

        Args:
            prompt: Prompt gerado.

        Returns:
            Lista de mensagens no formato Ollama.
        """
        messages = [{"role": "system", "content": prompt.system_prompt}]

        if prompt.context:
            content = f"{prompt.context}\n\n{prompt.user_prompt}"
            messages.append({"role": "user", "content": content})
        else:
            messages.append({"role": "user", "content": prompt.user_prompt})

        return messages

    def _execute_with_tools(
        self,
        messages: list[dict[str, str]],
        model: str,
        tools: list[dict[str, Any]],
    ) -> RunnerResult:
        """Executa o modelo com suporte a tool calling.

        Implementa o loop de tool calling:
        1. Envia prompt para o modelo
        2. Se modelo pedir tool, executa e retorna resultado
        3. Modelo gera resposta final

        Args:
            messages: Lista de mensagens.
            model: Nome do modelo.
            tools: Lista de tools disponíveis.

        Returns:
            RunnerResult com os resultados.
        """
        tool_calls_results: list[ToolCallResult] = []
        call_order = 0

        # Primeira chamada ao modelo
        response = self._client.chat(
            model=model,
            messages=messages,
            tools=tools,
            options=self.default_options,
        )

        # Verifica se o modelo quer chamar tools
        while response.message.tool_calls:
            # Processa cada tool call
            for tool_call in response.message.tool_calls:
                call_order += 1
                tool_name = tool_call.function.name
                tool_args = tool_call.function.arguments

                # Executa a tool (mock)
                tool_result = get_mock_response(tool_name, tool_args)

                tool_calls_results.append(
                    ToolCallResult(
                        tool_name=tool_name,
                        arguments=tool_args,
                        result=tool_result,
                        sequence_order=call_order,
                    )
                )

                # Adiciona a chamada e resposta ao histórico
                messages.append(response.message.model_dump())
                messages.append({
                    "role": "tool",
                    "content": json.dumps(tool_result),
                })

            # Chama o modelo novamente com os resultados das tools
            response = self._client.chat(
                model=model,
                messages=messages,
                tools=tools,
                options=self.default_options,
            )

        # Extrai informações da resposta final
        response_text = response.message.content or ""

        # Estima tokens (Ollama nem sempre retorna)
        input_tokens = getattr(response, "prompt_eval_count", None)
        output_tokens = getattr(response, "eval_count", None)

        return RunnerResult(
            success=True,
            response_text=response_text,
            tool_calls=tool_calls_results,
            raw_response=response.model_dump(),
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )

    def list_models(self) -> list[str]:
        """Lista modelos disponíveis no Ollama.

        Returns:
            Lista de nomes de modelos.
        """
        try:
            response = self._client.list()
            return [model.model for model in response.models]
        except Exception:
            return []

    def is_available(self) -> bool:
        """Verifica se o Ollama está disponível.

        Returns:
            True se o servidor Ollama está acessível.
        """
        try:
            self._client.list()
            return True
        except Exception:
            return False

    def check_model_exists(self, model: str) -> bool:
        """Verifica se um modelo específico está disponível.

        Args:
            model: Nome do modelo.

        Returns:
            True se o modelo está instalado.
        """
        models = self.list_models()
        return model in models or any(m.startswith(model.split(":")[0]) for m in models)
