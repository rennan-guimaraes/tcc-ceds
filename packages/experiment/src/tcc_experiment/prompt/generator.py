"""Gerador de prompts com níveis de poluição.

Este módulo implementa a lógica central do experimento: gerar prompts
com diferentes níveis de contexto redundante para testar a degradação
da capacidade de tool calling dos LLMs.
"""

import hashlib
from dataclasses import dataclass
from typing import Any

from tcc_experiment.prompt.templates import PromptTemplate, get_template


@dataclass
class GeneratedPrompt:
    """Prompt gerado com metadados.

    Attributes:
        system_prompt: Prompt do sistema (instruções).
        user_prompt: Pergunta do usuário.
        context: Contexto poluído (pode ser None se pollution=0).
        pollution_level: Nível de poluição aplicado (0-100).
        template_name: Nome do template usado.
        expected_tool: Tool que deveria ser chamada.
        expected_value: Valor correto (da tool).
        context_value: Valor armadilha (do contexto).
        prompt_hash: Hash SHA256 do prompt completo (reprodutibilidade).
        context_repetitions: Número de vezes que o contexto foi repetido.
    """

    system_prompt: str
    user_prompt: str
    context: str | None
    pollution_level: float
    template_name: str
    expected_tool: str
    expected_value: str
    context_value: str
    prompt_hash: str
    context_repetitions: int

    @property
    def full_prompt(self) -> str:
        """Retorna o prompt completo (sistema + contexto + usuário)."""
        parts = [self.system_prompt]
        if self.context:
            parts.append(self.context)
        parts.append(self.user_prompt)
        return "\n\n".join(parts)


class PromptGenerator:
    """Gerador de prompts com diferentes níveis de poluição.

    O gerador cria prompts variando a quantidade de contexto redundante
    para testar a hipótese de que mais contexto degrada o tool calling.

    Attributes:
        template: Template base para geração.
        expected_value: Valor correto que a tool deveria retornar.

    Example:
        >>> generator = PromptGenerator("stock_price_query")
        >>> prompt = generator.generate(pollution_level=40.0)
        >>> print(prompt.context_repetitions)
        3
    """

    # Mapeamento de nível de poluição para número de repetições
    POLLUTION_REPETITIONS: dict[float, int] = {
        0.0: 0,    # Sem contexto
        20.0: 1,   # Contexto 1x
        40.0: 3,   # Contexto 3x
        60.0: 5,   # Contexto 5x
        80.0: 8,   # Contexto 8x (opcional)
        100.0: 12, # Contexto 12x (opcional)
    }

    def __init__(
        self,
        template_name: str = "stock_price_query",
        expected_value: str = "R$ 38,50",
        variables_override: dict[str, str] | None = None,
    ) -> None:
        """Inicializa o gerador.

        Args:
            template_name: Nome do template a usar.
            expected_value: Valor correto esperado da tool.
            variables_override: Valores para sobrescrever no template.
        """
        self.template = get_template(template_name)
        self.expected_value = expected_value
        self.variables = {**self.template.variables}
        if variables_override:
            self.variables.update(variables_override)

    def generate(
        self,
        pollution_level: float,
        variables_override: dict[str, Any] | None = None,
    ) -> GeneratedPrompt:
        """Gera um prompt com o nível de poluição especificado.

        Args:
            pollution_level: Nível de poluição (0.0 a 100.0).
            variables_override: Valores para sobrescrever nesta geração.

        Returns:
            GeneratedPrompt com todos os metadados.

        Raises:
            ValueError: Se o nível de poluição for inválido.
        """
        if not 0.0 <= pollution_level <= 100.0:
            raise ValueError(
                f"Nível de poluição deve estar entre 0 e 100, recebido: {pollution_level}"
            )

        # Mescla variáveis
        variables = {**self.variables}
        if variables_override:
            variables.update(variables_override)

        # Gera componentes do prompt
        system_prompt = self._format_template(self.template.system_prompt, variables)
        user_prompt = self._format_template(self.template.user_prompt, variables)

        # Gera contexto poluído
        context, repetitions = self._generate_polluted_context(
            pollution_level, variables
        )

        # Calcula hash para reprodutibilidade
        full_content = f"{system_prompt}\n{context or ''}\n{user_prompt}"
        prompt_hash = hashlib.sha256(full_content.encode()).hexdigest()

        return GeneratedPrompt(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            context=context,
            pollution_level=pollution_level,
            template_name=self.template.name,
            expected_tool=self.template.expected_tool,
            expected_value=self.expected_value,
            context_value=variables.get("context_price", ""),
            prompt_hash=prompt_hash,
            context_repetitions=repetitions,
        )

    def _generate_polluted_context(
        self,
        pollution_level: float,
        variables: dict[str, Any],
    ) -> tuple[str | None, int]:
        """Gera o contexto com o nível de poluição especificado.

        Args:
            pollution_level: Nível de poluição (0-100).
            variables: Variáveis para substituição.

        Returns:
            Tupla (contexto_poluido, numero_de_repeticoes).
        """
        repetitions = self._get_repetitions(pollution_level)

        if repetitions == 0:
            return None, 0

        # Gera o bloco de contexto base
        base_context = self._format_template(
            self.template.context_template, variables
        )

        # Cria separador entre repetições
        separator = "\n\n" + "─" * 78 + "\n" + "      [CÓPIA DO RELATÓRIO PARA ARQUIVO]\n" + "─" * 78 + "\n\n"

        # Repete o contexto
        if repetitions == 1:
            return base_context, 1

        contexts = [base_context]
        for i in range(1, repetitions):
            # Adiciona pequenas variações para simular cópias
            variation = self._add_context_variation(base_context, i)
            contexts.append(variation)

        return separator.join(contexts), repetitions

    def _add_context_variation(self, context: str, index: int) -> str:
        """Adiciona pequenas variações ao contexto para simular cópias.

        Args:
            context: Contexto original.
            index: Índice da cópia (1, 2, 3...).

        Returns:
            Contexto com pequena variação.
        """
        # Adiciona um header indicando que é uma cópia arquivada
        header = f"[Cópia arquivada #{index + 1} - Gerada automaticamente pelo sistema]"
        return f"{header}\n{context}"

    def _get_repetitions(self, pollution_level: float) -> int:
        """Obtém o número de repetições para um nível de poluição.

        Args:
            pollution_level: Nível de poluição (0-100).

        Returns:
            Número de repetições do contexto.
        """
        # Se o nível exato existe no mapeamento, usa ele
        if pollution_level in self.POLLUTION_REPETITIONS:
            return self.POLLUTION_REPETITIONS[pollution_level]

        # Caso contrário, interpola
        levels = sorted(self.POLLUTION_REPETITIONS.keys())
        for i, level in enumerate(levels):
            if pollution_level < level:
                if i == 0:
                    return self.POLLUTION_REPETITIONS[levels[0]]
                # Interpola entre o nível anterior e o atual
                prev_level = levels[i - 1]
                prev_reps = self.POLLUTION_REPETITIONS[prev_level]
                curr_reps = self.POLLUTION_REPETITIONS[level]
                ratio = (pollution_level - prev_level) / (level - prev_level)
                return int(prev_reps + ratio * (curr_reps - prev_reps))

        return self.POLLUTION_REPETITIONS[levels[-1]]

    def _format_template(self, template: str, variables: dict[str, Any]) -> str:
        """Substitui placeholders no template.

        Args:
            template: Template com placeholders {var}.
            variables: Dicionário de variáveis.

        Returns:
            Template com variáveis substituídas.
        """
        result = template
        for key, value in variables.items():
            result = result.replace(f"{{{key}}}", str(value))
        return result

    def get_pollution_levels(self) -> list[float]:
        """Retorna os níveis de poluição padrão.

        Returns:
            Lista de níveis de poluição disponíveis.
        """
        return sorted(self.POLLUTION_REPETITIONS.keys())


def create_generator(
    template_name: str = "stock_price_query",
    expected_value: str = "R$ 38,50",
    **variables: str,
) -> PromptGenerator:
    """Factory function para criar um gerador de prompts.

    Args:
        template_name: Nome do template.
        expected_value: Valor esperado da tool.
        **variables: Variáveis para o template.

    Returns:
        PromptGenerator configurado.

    Example:
        >>> gen = create_generator(ticker="VALE3", context_price="R$ 60,00")
        >>> prompt = gen.generate(40.0)
    """
    return PromptGenerator(
        template_name=template_name,
        expected_value=expected_value,
        variables_override=variables if variables else None,
    )
