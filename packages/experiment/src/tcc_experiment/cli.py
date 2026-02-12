"""Interface de linha de comando para o experimento.

Utiliza Typer para criar uma CLI amigável com comandos
para executar experimentos e visualizar resultados.
"""

import contextlib
from typing import Annotated

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
        bool | None,
        typer.Option("--version", "-v", help="Mostra a versao e sai"),
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

    table = Table(title="Configuracoes do Experimento")
    table.add_column("Parametro", style="cyan")
    table.add_column("Valor", style="green")

    table.add_row("Database URL", str(settings.database_url))
    table.add_row("Ollama Host", settings.ollama_host)
    table.add_row("Ollama num_ctx", str(settings.ollama_num_ctx))
    table.add_row("Log Level", settings.log_level)
    table.add_row("Iteracoes Padrao", str(settings.default_iterations))
    table.add_row("Niveis de Poluicao", str(settings.pollution_levels))
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
            help="Modelos a testar (separados por virgula)",
        ),
    ] = "qwen3:4b",
    iterations: Annotated[
        int,
        typer.Option(
            "--iterations", "-i",
            help="Numero de iteracoes por condicao",
        ),
    ] = 5,
    pollution_levels: Annotated[
        str | None,
        typer.Option(
            "--pollution-levels", "-p",
            help="Niveis de poluicao (separados por virgula)",
        ),
    ] = None,
    hypothesis: Annotated[
        str,
        typer.Option(
            "--hypothesis", "-h",
            help="Hipotese sendo testada (H1, H2, H3)",
        ),
    ] = "H1",
    difficulty: Annotated[
        str,
        typer.Option(
            "--difficulty", "-d",
            help="Nivel de dificuldade (neutral, counterfactual, adversarial)",
        ),
    ] = "neutral",
    tool_set: Annotated[
        str,
        typer.Option(
            "--tool-set", "-t",
            help="Conjunto de tools (base, expanded)",
        ),
    ] = "base",
    context_placement: Annotated[
        str,
        typer.Option(
            "--context-placement",
            help="Posicionamento do contexto (user, system)",
        ),
    ] = "user",
    adversarial_variant: Annotated[
        str,
        typer.Option(
            "--adversarial-variant",
            help="Variante adversarial (with_timestamp, without_timestamp)",
        ),
    ] = "with_timestamp",
    no_db: Annotated[
        bool,
        typer.Option(
            "--no-db",
            help="Nao salva no banco de dados",
        ),
    ] = False,
    dry_run: Annotated[
        bool,
        typer.Option(
            "--dry-run",
            help="Simula execucao sem chamar os modelos",
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
        console.print("\n[bold blue]Configuracao do Experimento (Dry Run)[/bold blue]")
        console.print(f"  Nome: {name}")
        console.print(f"  Modelos: {model_list}")
        console.print(f"  Iteracoes: {iterations}")
        console.print(f"  Niveis de poluicao: {levels}")
        console.print(f"  Hipotese: {hypothesis}")
        console.print(f"  Dificuldade: {difficulty}")
        console.print(f"  Tool Set: {tool_set}")
        console.print(f"  Context Placement: {context_placement}")
        console.print(f"  Adversarial Variant: {adversarial_variant}")
        console.print(f"  Salvar no DB: {not no_db}")

        total_executions = len(model_list) * len(levels) * iterations
        console.print(f"\n  [yellow]Total de execucoes: {total_executions}[/yellow]")
        console.print("\n[dim]Modo dry-run: nenhuma execucao real sera feita.[/dim]")
        return

    # Executa experimento
    config = ExperimentConfig(
        name=name,
        models=model_list,
        pollution_levels=levels,
        iterations=iterations,
        hypothesis=hypothesis,
        difficulty=difficulty,
        tool_set=tool_set,
        context_placement=context_placement,
        adversarial_variant=adversarial_variant,
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
            help="Nivel de poluicao (%)",
        ),
    ] = 0.0,
    difficulty: Annotated[
        str,
        typer.Option(
            "--difficulty", "-d",
            help="Nivel de dificuldade (neutral, counterfactual, adversarial)",
        ),
    ] = "neutral",
    tool_set: Annotated[
        str,
        typer.Option(
            "--tool-set", "-t",
            help="Conjunto de tools (base, expanded)",
        ),
    ] = "base",
    context_placement: Annotated[
        str,
        typer.Option(
            "--context-placement",
            help="Posicionamento do contexto (user, system)",
        ),
    ] = "user",
    adversarial_variant: Annotated[
        str,
        typer.Option(
            "--adversarial-variant",
            help="Variante adversarial (with_timestamp, without_timestamp)",
        ),
    ] = "with_timestamp",
    no_save: Annotated[
        bool,
        typer.Option(
            "--no-save",
            help="Nao salvar no banco de dados",
        ),
    ] = False,
) -> None:
    """Executa um teste rapido (1 execucao)."""
    from tcc_experiment.database.repository import ExperimentRepository
    from tcc_experiment.evaluator import classify_result
    from tcc_experiment.prompt import create_generator
    from tcc_experiment.prompt.templates import AdversarialVariant, DifficultyLevel
    from tcc_experiment.runner import OllamaRunner
    from tcc_experiment.runner.ollama import ContextPlacement
    from tcc_experiment.tools.definitions import ToolSet, get_tools_for_experiment

    save_to_db = not no_save

    console.print("\n[bold blue]Teste Rapido[/bold blue]")
    console.print(f"Modelo: {model}")
    console.print(f"Poluicao: {pollution}%")
    console.print(f"Dificuldade: {difficulty}")
    console.print(f"Tool Set: {tool_set}")
    console.print(f"Context Placement: {context_placement}")
    console.print(f"Adversarial Variant: {adversarial_variant}")
    console.print(f"Salvar no banco: {save_to_db}\n")

    gen = create_generator(
        difficulty=DifficultyLevel(difficulty),
        adversarial_variant=AdversarialVariant(adversarial_variant),
    )
    runner = OllamaRunner()

    if not runner.is_available():
        console.print("[red]Erro: Ollama nao esta disponivel![/red]")
        raise typer.Exit(1)

    prompt = gen.generate(pollution)
    tools = get_tools_for_experiment(ToolSet(tool_set))

    console.print(f"Prompt: {prompt.user_prompt}")
    console.print(f"Valor armadilha: {prompt.context_value}")
    console.print(f"Valor esperado: {prompt.expected_value}\n")

    with console.status("Executando..."):
        result = runner.run(
            prompt,
            model=model,
            tools=tools,
            context_placement=ContextPlacement(context_placement),
        )

    evaluation = classify_result(prompt, result)

    # Salva no banco
    execution_id = None
    if save_to_db:
        try:
            repo = ExperimentRepository()
            parts = model.split(":")
            model_name = parts[0]
            model_version = parts[1] if len(parts) > 1 else None
            model_id = repo.get_or_create_model(
                name=model_name,
                version=model_version,
                parameter_count=model_version.upper() if model_version else None,
            )
            experiment_id = repo.create_experiment(
                name=f"Quick Test - {model} - {difficulty}",
                hypothesis="H1",
                pollution_levels=[pollution],
                iterations=1,
            )
            repo.start_experiment(experiment_id)
            execution_id = repo.save_execution(
                experiment_id=experiment_id,
                model_id=model_id,
                prompt=prompt,
                result=result,
                evaluation=evaluation,
                iteration=1,
                difficulty=difficulty,
                tool_set=tool_set,
                context_placement=context_placement,
                adversarial_variant=adversarial_variant if difficulty == "adversarial" else None,
            )
            repo.finish_experiment(experiment_id, "completed")
            console.print(f"[green]Salvo no banco (experiment: {experiment_id})[/green]\n")
        except Exception as e:
            console.print(f"[yellow]Aviso: nao foi possivel salvar no banco: {e}[/yellow]\n")

    # Resultado
    table = Table(title="Resultado")
    table.add_column("Metrica", style="cyan")
    table.add_column("Valor", style="green")

    table.add_row("Classificacao", evaluation.classification.value)
    table.add_row("Chamou tool correta", str(evaluation.called_target_tool))
    table.add_row("Usou valor da tool", str(evaluation.used_tool_result))
    table.add_row("Ancorou no contexto", str(evaluation.anchored_on_context))
    table.add_row("Valor extraido", evaluation.extracted_value or "N/A")
    table.add_row("Confianca", f"{evaluation.confidence_score:.0%}")
    table.add_row("Latencia", f"{result.latency_ms}ms")
    table.add_row("Tool Call Count", str(result.tool_call_count))
    table.add_row("Tool Call Sequence", result.tool_call_sequence or "N/A")

    console.print(table)
    console.print(f"\n[dim]Razao: {evaluation.reasoning}[/dim]")

    if result.response_text:
        console.print("\n[bold]Resposta do modelo:[/bold]")
        console.print(result.response_text[:500])


DIFFICULTIES = ["neutral", "counterfactual", "adversarial"]
TOOL_CALLING_MODELS = ["qwen3:4b", "qwen3:8b"]
ALL_POLLUTION_LEVELS = [0.0, 20.0, 40.0, 60.0, 80.0, 100.0]


@app.command()
def quick_test_all(
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
            help="Nivel de poluicao (%)",
        ),
    ] = 40.0,
    tool_set: Annotated[
        str,
        typer.Option(
            "--tool-set", "-t",
            help="Conjunto de tools (base, expanded)",
        ),
    ] = "base",
    context_placement: Annotated[
        str,
        typer.Option(
            "--context-placement",
            help="Posicionamento do contexto (user, system)",
        ),
    ] = "user",
) -> None:
    """Teste rapido em todos os niveis de dificuldade (1 execucao cada)."""
    from tcc_experiment.evaluator import classify_result
    from tcc_experiment.prompt import create_generator
    from tcc_experiment.prompt.templates import AdversarialVariant, DifficultyLevel
    from tcc_experiment.runner import OllamaRunner
    from tcc_experiment.runner.ollama import ContextPlacement
    from tcc_experiment.tools.definitions import ToolSet, get_tools_for_experiment

    runner = OllamaRunner()

    if not runner.is_available():
        console.print("[red]Erro: Ollama nao esta disponivel![/red]")
        raise typer.Exit(1)

    console.print("\n[bold blue]Quick Test All[/bold blue]")
    console.print(f"Modelo: {model} | Poluicao: {pollution}%")
    console.print(f"Tool Set: {tool_set} | Context Placement: {context_placement}\n")

    tools = get_tools_for_experiment(ToolSet(tool_set))

    summary_table = Table(title="Resultados - Quick Test All")
    summary_table.add_column("Dificuldade", style="cyan")
    summary_table.add_column("Classificacao", style="green")
    summary_table.add_column("Chamou tool", justify="center")
    summary_table.add_column("Ancorou contexto", justify="center")
    summary_table.add_column("Tool Calls", justify="center")
    summary_table.add_column("Sequencia", justify="left")
    summary_table.add_column("Latencia", justify="right")

    for diff in DIFFICULTIES:
        console.print(f"[dim]Executando {diff}...[/dim]")
        gen = create_generator(
            difficulty=DifficultyLevel(diff),
            adversarial_variant=AdversarialVariant("with_timestamp"),
        )
        prompt = gen.generate(pollution)

        result = runner.run(
            prompt,
            model=model,
            tools=tools,
            context_placement=ContextPlacement(context_placement),
        )
        evaluation = classify_result(prompt, result)

        color = "green" if evaluation.classification.value == "STC" else "red"
        summary_table.add_row(
            diff,
            f"[{color}]{evaluation.classification.value}[/{color}]",
            "yes" if evaluation.called_target_tool else "no",
            "yes" if evaluation.anchored_on_context else "no",
            str(result.tool_call_count),
            result.tool_call_sequence or "N/A",
            f"{result.latency_ms}ms",
        )

    console.print(summary_table)


@app.command()
def run_all(
    models: Annotated[
        str | None,
        typer.Option(
            "--models", "-m",
            help="Modelos (separados por virgula). Default: qwen3:4b,qwen3:8b",
        ),
    ] = None,
    iterations: Annotated[
        int,
        typer.Option(
            "--iterations", "-i",
            help="Iteracoes por condicao",
        ),
    ] = 20,
    pollution_levels: Annotated[
        str | None,
        typer.Option(
            "--pollution-levels", "-p",
            help="Niveis de poluicao (separados por virgula). Default: 0,20,40,60,80,100",
        ),
    ] = None,
    hypothesis: Annotated[
        str,
        typer.Option(
            "--hypothesis", "-h",
            help="Hipotese sendo testada (H1, H2, H3)",
        ),
    ] = "H1",
    tool_sets: Annotated[
        str | None,
        typer.Option(
            "--tool-sets",
            help="Tool sets separados por virgula (base,expanded)",
        ),
    ] = None,
    context_placements: Annotated[
        str | None,
        typer.Option(
            "--context-placements",
            help="Context placements separados por virgula (user,system)",
        ),
    ] = None,
    adversarial_variants: Annotated[
        str | None,
        typer.Option(
            "--adversarial-variants",
            help="Variantes adversariais separadas por virgula (with_timestamp,without_timestamp)",
        ),
    ] = None,
    no_db: Annotated[
        bool,
        typer.Option(
            "--no-db",
            help="Nao salva no banco de dados",
        ),
    ] = False,
    dry_run: Annotated[
        bool,
        typer.Option(
            "--dry-run",
            help="Simula execucao sem chamar os modelos",
        ),
    ] = False,
) -> None:
    """Executa o experimento completo em todos os niveis de dificuldade."""
    from tcc_experiment.database.repository import ExperimentRepository
    from tcc_experiment.experiment import ExperimentConfig, ExperimentRunner

    model_list = (
        [m.strip() for m in models.split(",")]
        if models
        else TOOL_CALLING_MODELS
    )
    levels = (
        [float(p) for p in pollution_levels.split(",")]
        if pollution_levels
        else ALL_POLLUTION_LEVELS
    )

    tool_set_list = [t.strip() for t in tool_sets.split(",")] if tool_sets else ["base"]
    placement_list = [p.strip() for p in context_placements.split(",")] if context_placements else ["user"]
    variant_list = [v.strip() for v in adversarial_variants.split(",")] if adversarial_variants else ["with_timestamp"]

    # Calcula total considerando todas as dimensoes
    # Para cada dificuldade, adversarial_variants so se aplica a "adversarial"
    total = 0
    for diff in DIFFICULTIES:
        variants = variant_list if diff == "adversarial" else ["with_timestamp"]
        total += len(model_list) * len(levels) * iterations * len(tool_set_list) * len(placement_list) * len(variants)

    console.print("\n[bold blue]Experimento Completo v3[/bold blue]")
    console.print(f"Modelos: {model_list}")
    console.print(f"Iteracoes: {iterations}")
    console.print(f"Niveis poluicao: {levels}")
    console.print(f"Dificuldades: {DIFFICULTIES}")
    console.print(f"Tool Sets: {tool_set_list}")
    console.print(f"Context Placements: {placement_list}")
    console.print(f"Adversarial Variants: {variant_list}")
    console.print(f"[yellow]Total de execucoes: {total}[/yellow]\n")

    if dry_run:
        console.print("[dim]Modo dry-run: nenhuma execucao real sera feita.[/dim]")
        return

    # Cria um unico experimento e compartilha entre as combinacoes
    save_to_db = not no_db
    repo = None
    experiment_id = None

    if save_to_db:
        try:
            repo = ExperimentRepository()
            experiment_id = repo.create_experiment(
                name=f"v3 Completo - {hypothesis}",
                hypothesis=hypothesis,
                description=f"Experimento v3 com 3 niveis de dificuldade: {', '.join(DIFFICULTIES)}",
                pollution_levels=levels,
                iterations=iterations,
            )
            repo.start_experiment(experiment_id)
            console.print(f"[green]Experimento criado: {experiment_id}[/green]\n")
        except Exception as e:
            console.print(f"[yellow]Aviso: Nao foi possivel salvar no banco: {e}[/yellow]")
            console.print("[yellow]Continuando sem persistencia...[/yellow]\n")
            save_to_db = False

    all_records = []

    for diff in DIFFICULTIES:
        for ts in tool_set_list:
            for cp in placement_list:
                variants = variant_list if diff == "adversarial" else ["with_timestamp"]
                for av in variants:
                    console.print(f"\n[bold magenta]{'=' * 60}[/bold magenta]")
                    console.print(f"[bold magenta]  Dificuldade: {diff.upper()} | Tool Set: {ts} | Placement: {cp} | Variant: {av}[/bold magenta]")
                    console.print(f"[bold magenta]{'=' * 60}[/bold magenta]\n")

                    exp_config = ExperimentConfig(
                        name=f"v3 Completo - {hypothesis}",
                        models=model_list,
                        pollution_levels=levels,
                        iterations=iterations,
                        hypothesis=hypothesis,
                        difficulty=diff,
                        tool_set=ts,
                        context_placement=cp,
                        adversarial_variant=av,
                    )

                    runner = ExperimentRunner(
                        exp_config,
                        save_to_db=save_to_db,
                        console=console,
                        experiment_id=experiment_id,
                        repo=repo,
                    )
                    records = runner.run()
                    all_records.extend(records)

    # Finaliza experimento no banco
    if save_to_db and repo and experiment_id:
        with contextlib.suppress(Exception):
            repo.finish_experiment(experiment_id, "completed")

    # Resumo consolidado final
    if len(DIFFICULTIES) > 1:
        _print_consolidated_summary(all_records, experiment_id, console)

    console.print(f"\n[bold green]Experimento completo finalizado! ({total} execucoes)[/bold green]")
    if experiment_id:
        console.print(f"[green]Use para consultar: tcc-experiment results -e {experiment_id}[/green]")


def _print_consolidated_summary(
    records: list,
    experiment_id: object,  # noqa: ARG001
    console: Console,
) -> None:
    """Imprime resumo consolidado de todas as dificuldades."""
    from rich.table import Table

    summary: dict[str, dict[str, dict[float, dict[str, int]]]] = {}

    for record in records:
        diff = record.difficulty
        if diff not in summary:
            summary[diff] = {}
        if record.model not in summary[diff]:
            summary[diff][record.model] = {}
        if record.pollution_level not in summary[diff][record.model]:
            summary[diff][record.model][record.pollution_level] = {
                "STC": 0, "FNC": 0, "FWT": 0, "FH": 0, "total": 0,
            }

        summary[diff][record.model][record.pollution_level][record.classification] += 1
        summary[diff][record.model][record.pollution_level]["total"] += 1

    table = Table(title="Resumo Consolidado - Todas as Dificuldades")
    table.add_column("Dificuldade", style="magenta")
    table.add_column("Modelo", style="cyan")
    table.add_column("Poluicao", justify="right")
    table.add_column("STC", justify="right", style="green")
    table.add_column("FNC", justify="right", style="yellow")
    table.add_column("FWT", justify="right", style="red")
    table.add_column("FH", justify="right", style="red")
    table.add_column("Taxa Sucesso", justify="right")

    for diff in sorted(summary.keys()):
        for model, levels in summary[diff].items():
            for pollution, counts in sorted(levels.items()):
                total_count = counts["total"]
                success_rate = (counts["STC"] / total_count * 100) if total_count > 0 else 0
                rate_style = "green" if success_rate >= 80 else "yellow" if success_rate >= 50 else "red"

                table.add_row(
                    diff,
                    model,
                    f"{pollution:.0f}%",
                    str(counts["STC"]),
                    str(counts["FNC"]),
                    str(counts["FWT"]),
                    str(counts["FH"]),
                    f"[{rate_style}]{success_rate:.0f}%[/{rate_style}]",
                )

    console.print(f"\n{'=' * 60}")
    console.print(table)


@app.command()
def results(
    experiment_id: Annotated[
        str | None,
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

        # Detecta se ha multiplas dificuldades
        difficulties = {row.get("difficulty") for row in summary}
        has_difficulty = any(d is not None for d in difficulties)
        # Detecta se ha colunas de novas dimensoes
        has_tool_set = any(row.get("tool_set") is not None for row in summary)
        has_context_placement = any(row.get("context_placement") is not None for row in summary)
        has_adversarial_variant = any(row.get("adversarial_variant") is not None for row in summary)

        table = Table(title=f"Resultados - {experiment_id[:8]}...")
        if has_difficulty:
            table.add_column("Dificuldade", style="magenta")
        if has_tool_set:
            table.add_column("Tool Set", style="blue")
        if has_context_placement:
            table.add_column("Placement", style="blue")
        if has_adversarial_variant:
            table.add_column("Adv. Variant", style="blue")
        table.add_column("Modelo", style="cyan")
        table.add_column("Poluicao", justify="right")
        table.add_column("Total", justify="right")
        table.add_column("STC", justify="right", style="green")
        table.add_column("FNC", justify="right", style="yellow")
        table.add_column("FWT", justify="right", style="red")
        table.add_column("FH", justify="right", style="red")
        table.add_column("Taxa Sucesso", justify="right")

        for row in summary:
            rate = row["success_rate_pct"]
            rate_style = "green" if rate >= 80 else "yellow" if rate >= 50 else "red"

            cols: list[str] = []
            if has_difficulty:
                cols.append(row.get("difficulty") or "N/A")
            if has_tool_set:
                cols.append(row.get("tool_set") or "N/A")
            if has_context_placement:
                cols.append(row.get("context_placement") or "N/A")
            if has_adversarial_variant:
                cols.append(row.get("adversarial_variant") or "N/A")
            cols.extend([
                row["model_name"],
                f"{row['pollution_level']:.0f}%",
                str(row["total_executions"]),
                str(row["success_count"]),
                str(row["no_call_count"]),
                str(row["wrong_tool_count"]),
                str(row["hallucination_count"]),
                f"[{rate_style}]{rate:.0f}%[/{rate_style}]",
            ])
            table.add_row(*cols)

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
        typer.Option("--output", "-o", help="Arquivo de saida"),
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
