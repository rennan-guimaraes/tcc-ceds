"""Orquestrador do experimento.

Coordena a execução completa do experimento de alucinação em tool calling,
gerenciando o ciclo de geração de prompts, execução e avaliação.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable
from uuid import UUID

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table

from tcc_experiment.database.repository import ExperimentRepository
from tcc_experiment.evaluator import classify_result, EvaluationResult
from tcc_experiment.prompt import PromptGenerator, GeneratedPrompt
from tcc_experiment.prompt.templates import AdversarialVariant, DifficultyLevel
from tcc_experiment.runner import OllamaRunner, RunnerResult
from tcc_experiment.runner.ollama import ContextPlacement
from tcc_experiment.tools.definitions import ToolSet, get_tools_for_experiment


@dataclass
class ExperimentConfig:
    """Configuração do experimento.

    Attributes:
        name: Nome do experimento.
        models: Lista de modelos a testar.
        pollution_levels: Níveis de poluição (%).
        iterations: Iterações por condição.
        hypothesis: Hipótese sendo testada (H1, H2, H3).
        tool_set: Conjunto de tools (base=4, expanded=8).
        context_placement: Onde posicionar o contexto (user ou system).
        adversarial_variant: Variante adversarial (com/sem timestamp).
    """

    name: str
    models: list[str] = field(default_factory=lambda: ["qwen3:4b"])
    pollution_levels: list[float] = field(default_factory=lambda: [0.0, 20.0, 40.0, 60.0])
    iterations: int = 5
    hypothesis: str = "H1"
    description: str | None = None
    difficulty: str = "neutral"
    tool_set: str = "base"
    context_placement: str = "user"
    adversarial_variant: str = "with_timestamp"


@dataclass
class ExecutionRecord:
    """Registro de uma execução individual."""

    model: str
    pollution_level: float
    iteration: int
    classification: str
    success: bool
    called_tool: bool
    latency_ms: int
    extracted_value: str | None
    difficulty: str = "neutral"
    tool_set: str = "base"
    context_placement: str = "user"
    adversarial_variant: str = "with_timestamp"
    tool_call_count: int = 0
    tool_call_sequence: str = ""


class ExperimentRunner:
    """Executor de experimentos.

    Gerencia a execução completa de um experimento, coordenando
    todos os componentes e salvando resultados.

    Example:
        >>> config = ExperimentConfig(name="Teste H1", models=["qwen3:4b"])
        >>> runner = ExperimentRunner(config)
        >>> results = runner.run()
    """

    def __init__(
        self,
        config: ExperimentConfig,
        save_to_db: bool = True,
        console: Console | None = None,
        experiment_id: UUID | None = None,
        repo: ExperimentRepository | None = None,
    ) -> None:
        """Inicializa o executor.

        Args:
            config: Configuração do experimento.
            save_to_db: Se deve salvar no banco de dados.
            console: Console Rich para output.
            experiment_id: ID de experimento existente (para agrupar múltiplas dificuldades).
            repo: Repositório existente (para compartilhar entre runners).
        """
        self.config = config
        self.save_to_db = save_to_db
        self.console = console or Console()

        difficulty = DifficultyLevel(config.difficulty)
        adversarial_variant = AdversarialVariant(config.adversarial_variant)
        self.generator = PromptGenerator(difficulty=difficulty, adversarial_variant=adversarial_variant)
        self.ollama = OllamaRunner()
        self.tools = get_tools_for_experiment(ToolSet(config.tool_set))
        self.context_placement = ContextPlacement(config.context_placement)
        self.repo = repo or (ExperimentRepository() if save_to_db else None)

        self.records: list[ExecutionRecord] = []
        self.experiment_id = experiment_id
        self._owns_experiment = experiment_id is None

    def run(self) -> list[ExecutionRecord]:
        """Executa o experimento completo.

        Returns:
            Lista de registros de execução.
        """
        self.console.print(f"\n[bold blue]Experimento: {self.config.name}[/bold blue]")
        self.console.print(f"Hipótese: {self.config.hypothesis}")
        self.console.print(f"Dificuldade: {self.config.difficulty}")
        self.console.print(f"Tool set: {self.config.tool_set}")
        self.console.print(f"Context placement: {self.config.context_placement}")
        if self.config.difficulty == "adversarial":
            self.console.print(f"Adversarial variant: {self.config.adversarial_variant}")
        self.console.print(f"Modelos: {self.config.models}")
        self.console.print(f"Níveis de poluição: {self.config.pollution_levels}")
        self.console.print(f"Iterações por condição: {self.config.iterations}")

        total_executions = (
            len(self.config.models) *
            len(self.config.pollution_levels) *
            self.config.iterations
        )
        self.console.print(f"[yellow]Total de execuções: {total_executions}[/yellow]\n")

        # Verifica Ollama
        if not self.ollama.is_available():
            self.console.print("[red]Erro: Ollama não está disponível![/red]")
            return []

        # Cria experimento no banco (apenas se não recebeu um ID externo)
        if self.save_to_db and self.repo and self._owns_experiment:
            try:
                self.experiment_id = self.repo.create_experiment(
                    name=self.config.name,
                    hypothesis=self.config.hypothesis,
                    description=self.config.description,
                    pollution_levels=self.config.pollution_levels,
                    iterations=self.config.iterations,
                )
                self.repo.start_experiment(self.experiment_id)
                self.console.print(f"[green]Experimento criado: {self.experiment_id}[/green]\n")
            except Exception as e:
                self.console.print(f"[yellow]Aviso: Não foi possível salvar no banco: {e}[/yellow]")
                self.console.print("[yellow]Continuando sem persistência...[/yellow]\n")
                self.save_to_db = False

        # Executa
        self.records = []

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=self.console,
        ) as progress:
            task = progress.add_task("Executando...", total=total_executions)

            for model in self.config.models:
                model_id = None
                if self.save_to_db and self.repo:
                    try:
                        # Extrai info do modelo
                        parts = model.split(":")
                        name = parts[0]
                        version = parts[1] if len(parts) > 1 else None
                        model_id = self.repo.get_or_create_model(
                            name=name,
                            version=version,
                            parameter_count=version.upper() if version else None,
                        )
                    except Exception:
                        pass

                for pollution in self.config.pollution_levels:
                    for iteration in range(1, self.config.iterations + 1):
                        progress.update(
                            task,
                            description=f"{model} | {pollution}% | iter {iteration}"
                        )

                        record = self._run_single(
                            model=model,
                            model_id=model_id,
                            pollution_level=pollution,
                            iteration=iteration,
                        )
                        self.records.append(record)
                        progress.advance(task)

        # Finaliza experimento (apenas se este runner criou o experimento)
        if self.save_to_db and self.repo and self.experiment_id and self._owns_experiment:
            try:
                self.repo.finish_experiment(self.experiment_id, "completed")
            except Exception:
                pass

        # Mostra resumo
        self._print_summary()

        return self.records

    def _run_single(
        self,
        model: str,
        model_id: UUID | None,
        pollution_level: float,
        iteration: int,
    ) -> ExecutionRecord:
        """Executa uma única iteração.

        Args:
            model: Nome do modelo.
            model_id: ID do modelo no banco.
            pollution_level: Nível de poluição.
            iteration: Número da iteração.

        Returns:
            Registro da execução.
        """
        # Gera prompt
        prompt = self.generator.generate(pollution_level)

        # Executa
        result = self.ollama.run(
            prompt,
            model=model,
            tools=self.tools,
            context_placement=self.context_placement,
        )

        # Avalia
        evaluation = classify_result(prompt, result)

        # Salva no banco
        if self.save_to_db and self.repo and self.experiment_id and model_id:
            try:
                self.repo.save_execution(
                    experiment_id=self.experiment_id,
                    model_id=model_id,
                    prompt=prompt,
                    result=result,
                    evaluation=evaluation,
                    iteration=iteration,
                    difficulty=self.config.difficulty,
                    tool_set=self.config.tool_set,
                    context_placement=self.config.context_placement,
                    adversarial_variant=self.config.adversarial_variant if self.config.difficulty == "adversarial" else None,
                )
            except Exception:
                pass

        return ExecutionRecord(
            model=model,
            pollution_level=pollution_level,
            iteration=iteration,
            classification=evaluation.classification.value,
            success=evaluation.classification.value == "STC",
            called_tool=evaluation.called_target_tool,
            latency_ms=result.latency_ms or 0,
            extracted_value=evaluation.extracted_value,
            difficulty=self.config.difficulty,
            tool_set=self.config.tool_set,
            context_placement=self.config.context_placement,
            adversarial_variant=self.config.adversarial_variant,
            tool_call_count=evaluation.tool_call_count,
            tool_call_sequence=evaluation.tool_call_sequence,
        )

    def _print_summary(self) -> None:
        """Imprime resumo dos resultados."""
        self.console.print("\n")

        # Agrupa por dificuldade, modelo e poluição
        summary: dict[str, dict[str, dict[float, dict[str, int]]]] = {}

        for record in self.records:
            diff = record.difficulty
            if diff not in summary:
                summary[diff] = {}
            if record.model not in summary[diff]:
                summary[diff][record.model] = {}
            if record.pollution_level not in summary[diff][record.model]:
                summary[diff][record.model][record.pollution_level] = {
                    "STC": 0, "FNC": 0, "FWT": 0, "FH": 0, "total": 0, "latency_sum": 0
                }

            summary[diff][record.model][record.pollution_level][record.classification] += 1
            summary[diff][record.model][record.pollution_level]["total"] += 1
            summary[diff][record.model][record.pollution_level]["latency_sum"] += record.latency_ms

        # Cria tabela
        has_multiple_difficulties = len(summary) > 1
        table = Table(title="Resultados do Experimento")
        if has_multiple_difficulties:
            table.add_column("Dificuldade", style="magenta")
        table.add_column("Modelo", style="cyan")
        table.add_column("Poluição", justify="right")
        table.add_column("STC", justify="right", style="green")
        table.add_column("FNC", justify="right", style="yellow")
        table.add_column("FWT", justify="right", style="red")
        table.add_column("FH", justify="right", style="red")
        table.add_column("Taxa Sucesso", justify="right")
        table.add_column("Latência Média", justify="right")

        for diff in sorted(summary.keys()):
            for model, levels in summary[diff].items():
                for pollution, counts in sorted(levels.items()):
                    total = counts["total"]
                    success_rate = (counts["STC"] / total * 100) if total > 0 else 0
                    avg_latency = counts["latency_sum"] / total if total > 0 else 0

                    rate_style = "green" if success_rate >= 80 else "yellow" if success_rate >= 50 else "red"

                    row: list[str] = []
                    if has_multiple_difficulties:
                        row.append(diff)
                    row.extend([
                        model,
                        f"{pollution:.0f}%",
                        str(counts["STC"]),
                        str(counts["FNC"]),
                        str(counts["FWT"]),
                        str(counts["FH"]),
                        f"[{rate_style}]{success_rate:.0f}%[/{rate_style}]",
                        f"{avg_latency/1000:.1f}s",
                    ])
                    table.add_row(*row)

        self.console.print(table)

        if self.experiment_id:
            self.console.print(f"\n[dim]Experimento ID: {self.experiment_id}[/dim]")


def run_experiment(
    name: str = "Experimento H1",
    models: list[str] | None = None,
    pollution_levels: list[float] | None = None,
    iterations: int = 5,
    hypothesis: str = "H1",
    difficulty: str = "neutral",
    save_to_db: bool = True,
    tool_set: str = "base",
    context_placement: str = "user",
    adversarial_variant: str = "with_timestamp",
) -> list[ExecutionRecord]:
    """Função conveniente para executar um experimento.

    Args:
        name: Nome do experimento.
        models: Modelos a testar.
        pollution_levels: Níveis de poluição.
        iterations: Iterações por condição.
        hypothesis: Hipótese sendo testada.
        difficulty: Nível de dificuldade.
        save_to_db: Se deve salvar no banco.
        tool_set: Conjunto de tools (base, expanded).
        context_placement: Posição do contexto (user, system).
        adversarial_variant: Variante adversarial (with_timestamp, without_timestamp).

    Returns:
        Lista de registros de execução.
    """
    config = ExperimentConfig(
        name=name,
        models=models or ["qwen3:4b"],
        pollution_levels=pollution_levels or [0.0, 20.0, 40.0, 60.0],
        iterations=iterations,
        hypothesis=hypothesis,
        difficulty=difficulty,
        tool_set=tool_set,
        context_placement=context_placement,
        adversarial_variant=adversarial_variant,
    )

    runner = ExperimentRunner(config, save_to_db=save_to_db)
    return runner.run()
