"""CLI entry point."""

from __future__ import annotations

import typer

from code_review_benchmark.cli.commands import evaluate, report, run

app = typer.Typer(
    name="crb",
    help="Code Review Benchmark — benchmark suite for AI code review tools.",
    no_args_is_help=True,
)

app.command(name="run")(run.run_cmd)
app.command(name="evaluate")(evaluate.evaluate_cmd)
app.command(name="report")(report.report_cmd)


@app.command()
def setup() -> None:
    """Verify tools are installed and API keys are set."""
    import os

    from rich.console import Console
    from rich.table import Table

    # Force runner registration
    import code_review_benchmark.runners.claude_reviewer  # noqa: F401
    import code_review_benchmark.runners.gemini_reviewer  # noqa: F401
    import code_review_benchmark.runners.openai_reviewer  # noqa: F401
    import code_review_benchmark.runners.pr_agent  # noqa: F401
    import code_review_benchmark.runners.shippie  # noqa: F401
    from code_review_benchmark.runners.registry import list_runners

    console = Console()
    table = Table(title="Tool Status")
    table.add_column("Tool")
    table.add_column("Available")
    table.add_column("Version Command")

    for runner in list_runners():
        available = runner.is_available()
        status = "[green]YES[/green]" if available else "[red]NO[/red]"
        table.add_row(runner.name, status, " ".join(runner.version_command))

    console.print(table)

    # Check API keys
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if api_key:
        console.print("[green]OPENAI_API_KEY[/green]: set")
    else:
        console.print(
            "[red]OPENAI_API_KEY[/red]: not set (needed for LLM judge and openai-reviewer)"
        )

    anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "")
    use_bedrock = os.environ.get("CRB_CLAUDE_USE_BEDROCK", "").lower() == "true"
    if anthropic_key:
        console.print("[green]ANTHROPIC_API_KEY[/green]: set")
    elif use_bedrock:
        console.print("[green]CRB_CLAUDE_USE_BEDROCK[/green]: enabled (using AWS credentials)")
    else:
        console.print(
            "[yellow]ANTHROPIC_API_KEY[/yellow]: not set "
            "(needed for claude-reviewer; or set CRB_CLAUDE_USE_BEDROCK=true)"
        )


@app.command(name="list-tools")
def list_tools() -> None:
    """Show registered tools and their availability."""
    from rich.console import Console

    import code_review_benchmark.runners.claude_reviewer  # noqa: F401
    import code_review_benchmark.runners.gemini_reviewer  # noqa: F401
    import code_review_benchmark.runners.openai_reviewer  # noqa: F401
    import code_review_benchmark.runners.pr_agent  # noqa: F401
    import code_review_benchmark.runners.shippie  # noqa: F401
    from code_review_benchmark.runners.registry import list_runners

    console = Console()
    for runner in list_runners():
        status = "available" if runner.is_available() else "not found"
        console.print(f"  {runner.name}: {status}")


@app.command(name="list-challenges")
def list_challenges_cmd() -> None:
    """Show all available challenges."""
    from pathlib import Path

    from rich.console import Console
    from rich.table import Table

    from code_review_benchmark.models.challenge import load_challenges

    console = Console()
    challenges_dir = Path(__file__).resolve().parents[3] / "challenges"

    if not challenges_dir.exists():
        console.print(f"[red]Challenges directory not found: {challenges_dir}[/red]")
        raise typer.Exit(1)

    challenges = load_challenges(challenges_dir)
    table = Table(title="Challenges")
    table.add_column("ID")
    table.add_column("Name")
    table.add_column("Language")
    table.add_column("Difficulty")
    table.add_column("Issues")

    for ch in challenges:
        table.add_row(ch.id, ch.name, ch.language, ch.difficulty.value, str(len(ch.issues)))

    console.print(table)


@app.command(name="validate-challenges")
def validate_challenges_cmd() -> None:
    """Validate all challenge definitions."""
    from pathlib import Path

    from rich.console import Console

    from code_review_benchmark.models.challenge import load_challenges

    console = Console()
    challenges_dir = Path(__file__).resolve().parents[3] / "challenges"
    challenges = load_challenges(challenges_dir)

    errors = 0
    for ch in challenges:
        if not ch.before_dir.exists():
            console.print(f"[red]{ch.id}: missing before/ directory[/red]")
            errors += 1
        if not ch.after_dir.exists():
            console.print(f"[red]{ch.id}: missing after/ directory[/red]")
            errors += 1
        if not ch.issues:
            console.print(f"[yellow]{ch.id}: no ground truth issues defined[/yellow]")
        else:
            console.print(f"[green]{ch.id}: OK ({len(ch.issues)} issues)[/green]")

    if errors:
        console.print(f"\n[red]{errors} error(s) found[/red]")
        raise typer.Exit(1)
    else:
        console.print(f"\n[green]All {len(challenges)} challenges valid[/green]")
