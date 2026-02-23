"""The `crb run` command — run benchmark tools against challenges."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.progress import Progress

console = Console()


def run_cmd(
    tools: Optional[str] = typer.Option(None, help="Comma-separated tool names to run"),
    challenges: Optional[str] = typer.Option(None, help="Comma-separated challenge IDs"),
    num_runs: int = typer.Option(0, "--runs", help="Runs per tool/challenge (0 = use env or 3)"),
    model: Optional[str] = typer.Option(None, help="LLM model to pass to tools"),
    output_dir: Optional[str] = typer.Option(None, "--output-dir", help="Custom output directory"),
) -> None:
    """Run all (or selected) tools against all (or selected) challenges."""
    # Lazy imports to keep CLI startup fast
    import code_review_benchmark.runners.coderabbit  # noqa: F401
    import code_review_benchmark.runners.pr_agent  # noqa: F401
    import code_review_benchmark.runners.shippie  # noqa: F401
    from code_review_benchmark.challenge_repo.builder import build_challenge_repo
    from code_review_benchmark.models.challenge import load_challenges
    from code_review_benchmark.runners.registry import available_tool_names, get_runner

    project_root = Path(__file__).resolve().parents[4]
    challenges_dir = project_root / "challenges"

    # Resolve num_runs
    if num_runs <= 0:
        num_runs = int(os.environ.get("CRB_NUM_RUNS", "3"))

    # Resolve model
    model = model or os.environ.get("CRB_TOOL_MODEL")

    # Load challenges
    challenge_ids = [c.strip() for c in challenges.split(",")] if challenges else None
    loaded = load_challenges(challenges_dir, ids=challenge_ids)
    if not loaded:
        console.print("[red]No challenges found.[/red]")
        raise typer.Exit(1)

    # Resolve tools
    tool_names = [t.strip() for t in tools.split(",")] if tools else available_tool_names()
    runners = []
    for name in tool_names:
        try:
            runner = get_runner(name)
            runners.append(runner)
        except KeyError:
            console.print(f"[red]Unknown tool: {name}[/red]")
            raise typer.Exit(1)

    # Create output directory
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    if output_dir:
        run_dir = Path(output_dir)
    else:
        run_dir = project_root / "results" / "runs" / timestamp
    run_dir.mkdir(parents=True, exist_ok=True)

    # Also create/update a 'latest' symlink
    latest = project_root / "results" / "latest"
    latest.unlink(missing_ok=True)
    latest.symlink_to(run_dir)

    console.print(f"Output: {run_dir}")
    console.print(f"Tools: {[r.name for r in runners]}")
    console.print(f"Challenges: {[c.id for c in loaded]}")
    console.print(f"Runs per pair: {num_runs}")
    console.print()

    total_tasks = len(runners) * len(loaded) * num_runs
    with Progress(console=console) as progress:
        task = progress.add_task("Running benchmark...", total=total_tasks)

        for challenge in loaded:
            for runner in runners:
                for run_idx in range(num_runs):
                    progress.update(
                        task,
                        description=f"{runner.name} × {challenge.id} (run {run_idx + 1})",
                    )

                    # Build temp repo
                    repo = build_challenge_repo(challenge)

                    try:
                        result = runner.run(
                            repo_path=repo.path,
                            pr_branch=repo.pr_branch,
                            main_branch=repo.main_branch,
                            model=model,
                        )
                    finally:
                        repo.cleanup()

                    # Save raw output
                    result_dir = run_dir / challenge.id / runner.name / f"run_{run_idx}"
                    result_dir.mkdir(parents=True, exist_ok=True)

                    (result_dir / "output.txt").write_text(result.output_text)
                    (result_dir / "stderr.txt").write_text(result.error)
                    (result_dir / "meta.json").write_text(
                        json.dumps(
                            {
                                "tool": result.tool,
                                "success": result.success,
                                "return_code": result.return_code,
                                "model": model,
                                "run_index": run_idx,
                            },
                            indent=2,
                        )
                    )

                    status = "[green]OK[/green]" if result.success else "[red]FAIL[/red]"
                    console.print(
                        f"  {runner.name} × {challenge.id} run {run_idx}: {status}"
                    )
                    progress.advance(task)

    console.print(f"\n[green]Done![/green] Results in {run_dir}")
