"""Interface de linha de comando para o experimento.

Utiliza Typer para criar uma CLI amigável com comandos
para executar experimentos e visualizar resultados.
"""

from typing import Annotated, Optional

import typer
from rich.console import Console
from rich.table import Table

from tcc_experiment import __version__
from tcc_experiment.config import get_settings

app = typer.Typer(
    name="tcc-experiment",
    help="Experimento de alucinação em tool calling - TCC CEDS/ITA",
    add_completion=False,
)
console = Console()


@app.callback()
def main(
    version: Annotated[
        Optional[bool],
        typer.Option("--version", "-v", help="Mostra a versão e sai"),
    ] = None,
) -> None:
    """TCC Experiment CLI - Alucinação em Tool Calling."""
    if version:
        console.print(f"tcc-experiment v{__version__}")
        raise typer.Exit()


@app.command()
def config() -> None:
    """Mostra as configurações atuais."""
    settings = get_settings()

    table = Table(title="Configurações do Experimento")
    table.add_column("Parâmetro", style="cyan")
    table.add_column("Valor", style="green")

    table.add_row("Database URL", str(settings.database_url))
    table.add_row("Ollama Host", settings.ollama_host)
    table.add_row("Ollama num_ctx", str(settings.ollama_num_ctx))
    table.add_row("Log Level", settings.log_level)
    table.add_row("Iterações Padrão", str(settings.default_iterations))
    table.add_row("Níveis de Poluição", str(settings.pollution_levels))
    table.add_row("Tool Alvo", settings.target_tool)
    table.add_row("Dificuldade", settings.difficulty_level)

    console.print(table)


@app.command()
def run(
    name: Annotated[
        str,
        typer.Option(
            "--name", "-n",
            help="Nome do experimento",
        ),
    ] = "Experimento H1",
    models: Annotated[
        str,
        typer.Option(
            "--models", "-m",
            help="Modelos a testar (separados por vírgula)",
        ),
    ] = "qwen3:4b",
    iterations: Annotated[
        int,
        typer.Option(
            "--iterations", "-i",
            help="Número de iterações por condição",
        ),
    ] = 5,
    pollution_levels: Annotated[
        Optional[str],
        typer.Option(
            "--pollution-levels", "-p",
            help="Níveis de poluição (separados por vírgula)",
        ),
    ] = None,
    hypothesis: Annotated[
        str,
        typer.Option(
            "--hypothesis", "-h",
            help="Hipótese sendo testada (H1, H2, H3)",
        ),
    ] = "H1",
    difficulty: Annotated[
        str,
        typer.Option(
            "--difficulty", "-d",
            help="Nível de dificuldade (neutral, counterfactual, adversarial)",
        ),
    ] = "neutral",
    no_db: Annotated[
        bool,
        typer.Option(
            "--no-db",
            help="Não salva no banco de dados",
        ),
    ] = False,
    dry_run: Annotated[
        bool,
        typer.Option(
            "--dry-run",
            help="Simula execução sem chamar os modelos",
        ),
    ] = False,
) -> None:
    """Executa o experimento de tool calling."""
    from tcc_experiment.experiment import ExperimentConfig, ExperimentRunner

    settings = get_settings()

    model_list = [m.strip() for m in models.split(",")]
    levels = (
        [float(p) for p in pollution_levels.split(",")]
        if pollution_levels
        else settings.pollution_levels
    )

    if dry_run:
        console.print("\n[bold blue]Configuração do Experimento (Dry Run)[/bold blue]")
        console.print(f"  Nome: {name}")
        console.print(f"  Modelos: {model_list}")
        console.print(f"  Iterações: {iterations}")
        console.print(f"  Níveis de poluição: {levels}")
        console.print(f"  Hipótese: {hypothesis}")
        console.print(f"  Dificuldade: {difficulty}")
        console.print(f"  Salvar no DB: {not no_db}")

        total_executions = len(model_list) * len(levels) * iterations
        console.print(f"\n  [yellow]Total de execuções: {total_executions}[/yellow]")
        console.print("\n[dim]Modo dry-run: nenhuma execução real será feita.[/dim]")
        return

    # Executa experimento
    config = ExperimentConfig(
        name=name,
        models=model_list,
        pollution_levels=levels,
        iterations=iterations,
        hypothesis=hypothesis,
        difficulty=difficulty,
    )

    runner = ExperimentRunner(config, save_to_db=not no_db, console=console)
    runner.run()


@app.command()
def quick_test(
    model: Annotated[
        str,
        typer.Option(
            "--model", "-m",
            help="Modelo a testar",
        ),
    ] = "qwen3:4b",
    pollution: Annotated[
        float,
        typer.Option(
            "--pollution", "-p",
            help="Nível de poluição (%)",
        ),
    ] = 0.0,
    difficulty: Annotated[
        str,
        typer.Option(
            "--difficulty", "-d",
            help="Nível de dificuldade (neutral, counterfactual, adversarial)",
        ),
    ] = "neutral",
) -> None:
    """Executa um teste rápido (1 execução)."""
    from tcc_experiment.prompt import create_generator
    from tcc_experiment.prompt.templates import DifficultyLevel
    from tcc_experiment.runner import OllamaRunner
    from tcc_experiment.evaluator import classify_result

    console.print(f"\n[bold blue]Teste Rápido[/bold blue]")
    console.print(f"Modelo: {model}")
    console.print(f"Poluição: {pollution}%")
    console.print(f"Dificuldade: {difficulty}\n")

    gen = create_generator(difficulty=DifficultyLevel(difficulty))
    runner = OllamaRunner()

    if not runner.is_available():
        console.print("[red]Erro: Ollama não está disponível![/red]")
        raise typer.Exit(1)

    prompt = gen.generate(pollution)
    console.print(f"Prompt: {prompt.user_prompt}")
    console.print(f"Valor armadilha: {prompt.context_value}")
    console.print(f"Valor esperado: {prompt.expected_value}\n")

    with console.status("Executando..."):
        result = runner.run(prompt, model=model)

    evaluation = classify_result(prompt, result)

    # Resultado
    table = Table(title="Resultado")
    table.add_column("Métrica", style="cyan")
    table.add_column("Valor", style="green")

    table.add_row("Classificação", evaluation.classification.value)
    table.add_row("Chamou tool correta", str(evaluation.called_target_tool))
    table.add_row("Usou valor da tool", str(evaluation.used_tool_result))
    table.add_row("Ancorou no contexto", str(evaluation.anchored_on_context))
    table.add_row("Valor extraído", evaluation.extracted_value or "N/A")
    table.add_row("Confiança", f"{evaluation.confidence_score:.0%}")
    table.add_row("Latência", f"{result.latency_ms}ms")

    console.print(table)
    console.print(f"\n[dim]Razão: {evaluation.reasoning}[/dim]")

    if result.response_text:
        console.print(f"\n[bold]Resposta do modelo:[/bold]")
        console.print(result.response_text[:500])


@app.command()
def results(
    experiment_id: Annotated[
        Optional[str],
        typer.Option(
            "--experiment-id", "-e",
            help="ID do experimento",
        ),
    ] = None,
) -> None:
    """Mostra resultados de um experimento."""
    if not experiment_id:
        console.print("[yellow]Use --experiment-id para especificar o experimento.[/yellow]")
        return

    from uuid import UUID
    from tcc_experiment.database import ExperimentRepository

    try:
        repo = ExperimentRepository()
        summary = repo.get_experiment_summary(UUID(experiment_id))

        if not summary:
            console.print("[yellow]Nenhum resultado encontrado.[/yellow]")
            return

        table = Table(title=f"Resultados - {experiment_id[:8]}...")
        table.add_column("Modelo", style="cyan")
        table.add_column("Poluição", justify="right")
        table.add_column("Total", justify="right")
        table.add_column("STC", justify="right", style="green")
        table.add_column("FNC", justify="right", style="yellow")
        table.add_column("FWT", justify="right", style="red")
        table.add_column("FH", justify="right", style="red")
        table.add_column("Taxa Sucesso", justify="right")

        for row in summary:
            table.add_row(
                row["model_name"],
                f"{row['pollution_level']:.0f}%",
                str(row["total_executions"]),
                str(row["success_count"]),
                str(row["no_call_count"]),
                str(row["wrong_tool_count"]),
                str(row["hallucination_count"]),
                f"{row['success_rate_pct']:.0f}%",
            )

        console.print(table)

    except Exception as e:
        console.print(f"[red]Erro ao buscar resultados: {e}[/red]")


@app.command()
def export(
    experiment_id: Annotated[
        str,
        typer.Option("--experiment-id", "-e", help="ID do experimento"),
    ],
    output: Annotated[
        str,
        typer.Option("--output", "-o", help="Arquivo de saída"),
    ] = "results.csv",
) -> None:
    """Exporta resultados para CSV."""
    import csv
    from uuid import UUID
    from tcc_experiment.database import ExperimentRepository

    try:
        repo = ExperimentRepository()
        results = repo.get_experiment_results(UUID(experiment_id))

        if not results:
            console.print("[yellow]Nenhum resultado encontrado.[/yellow]")
            return

        # Exporta para CSV
        with open(output, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=results[0].keys())
            writer.writeheader()
            writer.writerows(results)

        console.print(f"[green]Exportado {len(results)} registros para {output}[/green]")

    except Exception as e:
        console.print(f"[red]Erro ao exportar: {e}[/red]")


if __name__ == "__main__":
    app()
