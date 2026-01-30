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
from tcc_experiment.runner import OllamaRunner, RunnerResult


@dataclass
class ExperimentConfig:
    """Configuração do experimento.

    Attributes:
        name: Nome do experimento.
        models: Lista de modelos a testar.
        pollution_levels: Níveis de poluição (%).
        iterations: Iterações por condição.
        hypothesis: Hipótese sendo testada (H1, H2, H3).
    """

    name: str
    models: list[str] = field(default_factory=lambda: ["qwen3:4b"])
    pollution_levels: list[float] = field(default_factory=lambda: [0.0, 20.0, 40.0, 60.0])
    iterations: int = 5
    hypothesis: str = "H1"
    description: str | None = None


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
    ) -> None:
        """Inicializa o executor.

        Args:
            config: Configuração do experimento.
            save_to_db: Se deve salvar no banco de dados.
            console: Console Rich para output.
        """
        self.config = config
        self.save_to_db = save_to_db
        self.console = console or Console()

        self.generator = PromptGenerator()
        self.ollama = OllamaRunner()
        self.repo = ExperimentRepository() if save_to_db else None

        self.records: list[ExecutionRecord] = []
        self.experiment_id: UUID | None = None

    def run(self) -> list[ExecutionRecord]:
        """Executa o experimento completo.

        Returns:
            Lista de registros de execução.
        """
        self.console.print(f"\n[bold blue]Experimento: {self.config.name}[/bold blue]")
        self.console.print(f"Hipótese: {self.config.hypothesis}")
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

        # Cria experimento no banco
        if self.save_to_db and self.repo:
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

        # Finaliza experimento
        if self.save_to_db and self.repo and self.experiment_id:
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
        result = self.ollama.run(prompt, model=model)

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
                )
            except Exception as e:
                # Log mas não falha
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
        )

    def _print_summary(self) -> None:
        """Imprime resumo dos resultados."""
        self.console.print("\n")

        # Agrupa por modelo e poluição
        summary: dict[str, dict[float, dict[str, int]]] = {}

        for record in self.records:
            if record.model not in summary:
                summary[record.model] = {}
            if record.pollution_level not in summary[record.model]:
                summary[record.model][record.pollution_level] = {
                    "STC": 0, "FNC": 0, "FWT": 0, "FH": 0, "total": 0, "latency_sum": 0
                }

            summary[record.model][record.pollution_level][record.classification] += 1
            summary[record.model][record.pollution_level]["total"] += 1
            summary[record.model][record.pollution_level]["latency_sum"] += record.latency_ms

        # Cria tabela
        table = Table(title="Resultados do Experimento")
        table.add_column("Modelo", style="cyan")
        table.add_column("Poluição", justify="right")
        table.add_column("STC", justify="right", style="green")
        table.add_column("FNC", justify="right", style="yellow")
        table.add_column("FWT", justify="right", style="red")
        table.add_column("FH", justify="right", style="red")
        table.add_column("Taxa Sucesso", justify="right")
        table.add_column("Latência Média", justify="right")

        for model, levels in summary.items():
            for pollution, counts in sorted(levels.items()):
                total = counts["total"]
                success_rate = (counts["STC"] / total * 100) if total > 0 else 0
                avg_latency = counts["latency_sum"] / total if total > 0 else 0

                # Cor baseada na taxa de sucesso
                rate_style = "green" if success_rate >= 80 else "yellow" if success_rate >= 50 else "red"

                table.add_row(
                    model,
                    f"{pollution:.0f}%",
                    str(counts["STC"]),
                    str(counts["FNC"]),
                    str(counts["FWT"]),
                    str(counts["FH"]),
                    f"[{rate_style}]{success_rate:.0f}%[/{rate_style}]",
                    f"{avg_latency/1000:.1f}s",
                )

        self.console.print(table)

        if self.experiment_id:
            self.console.print(f"\n[dim]Experimento ID: {self.experiment_id}[/dim]")


def run_experiment(
    name: str = "Experimento H1",
    models: list[str] | None = None,
    pollution_levels: list[float] | None = None,
    iterations: int = 5,
    hypothesis: str = "H1",
    save_to_db: bool = True,
) -> list[ExecutionRecord]:
    """Função conveniente para executar um experimento.

    Args:
        name: Nome do experimento.
        models: Modelos a testar.
        pollution_levels: Níveis de poluição.
        iterations: Iterações por condição.
        hypothesis: Hipótese sendo testada.
        save_to_db: Se deve salvar no banco.

    Returns:
        Lista de registros de execução.
    """
    config = ExperimentConfig(
        name=name,
        models=models or ["qwen3:4b"],
        pollution_levels=pollution_levels or [0.0, 20.0, 40.0, 60.0],
        iterations=iterations,
        hypothesis=hypothesis,
    )

    runner = ExperimentRunner(config, save_to_db=save_to_db)
    return runner.run()
