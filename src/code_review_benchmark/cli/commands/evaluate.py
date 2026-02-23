"""The `crb evaluate` command — score stored results against ground truth."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

console = Console()


def evaluate_cmd(
    run_dir: str = typer.Option("results/latest", "--run-dir", help="Path to run results"),
    judge_model: Optional[str] = typer.Option(None, help="LLM model for evaluation judge"),
    skip_llm: bool = typer.Option(False, "--skip-llm", help="Use heuristic matching only"),
) -> None:
    """Evaluate stored run results against ground truth challenges."""
    from code_review_benchmark.evaluation.aggregator import aggregate_results
    from code_review_benchmark.evaluation.llm_judge import llm_judge_batch
    from code_review_benchmark.evaluation.matcher import heuristic_match
    from code_review_benchmark.evaluation.scorer import score_challenge_run
    from code_review_benchmark.models.challenge import load_challenges
    from code_review_benchmark.models.evaluation import ChallengeToolResult
    from code_review_benchmark.parsers.coderabbit import CodeRabbitParser
    from code_review_benchmark.parsers.pr_agent import PRAgentParser
    from code_review_benchmark.parsers.shippie import ShippieParser
    from code_review_benchmark.parsers.xai_review import XAIReviewParser
    from code_review_benchmark.runners.base import RunResult

    project_root = Path(__file__).resolve().parents[4]
    run_path = Path(run_dir) if Path(run_dir).is_absolute() else project_root / run_dir

    if not run_path.exists():
        console.print(f"[red]Run directory not found: {run_path}[/red]")
        raise typer.Exit(1)

    judge_model = judge_model or os.environ.get("CRB_JUDGE_MODEL", "gpt-4o")
    tool_model = os.environ.get("CRB_TOOL_MODEL", "")

    # Build parser lookup
    parsers = {
        "coderabbit": CodeRabbitParser(),
        "pr-agent": PRAgentParser(),
        "shippie": ShippieParser(),
        "xai-review": XAIReviewParser(),
    }

    # Load challenges
    challenges_dir = project_root / "challenges"
    all_challenges = {ch.id: ch for ch in load_challenges(challenges_dir)}

    all_results: list[ChallengeToolResult] = []

    # Walk the run directory structure: {challenge_id}/{tool}/{run_N}/
    for challenge_dir in sorted(run_path.iterdir()):
        if not challenge_dir.is_dir():
            continue
        challenge_id = challenge_dir.name
        challenge = all_challenges.get(challenge_id)
        if not challenge:
            console.print(f"[yellow]Skipping unknown challenge: {challenge_id}[/yellow]")
            continue

        for tool_dir in sorted(challenge_dir.iterdir()):
            if not tool_dir.is_dir():
                continue
            tool_name = tool_dir.name
            parser = parsers.get(tool_name)
            if not parser:
                console.print(f"[yellow]No parser for tool: {tool_name}[/yellow]")
                continue

            for run_dir_path in sorted(tool_dir.iterdir()):
                if not run_dir_path.is_dir():
                    continue

                output_file = run_dir_path / "output.txt"
                if not output_file.exists():
                    continue

                meta_file = run_dir_path / "meta.json"
                meta = json.loads(meta_file.read_text()) if meta_file.exists() else {}
                run_idx = meta.get("run_index", 0)

                # Parse output
                raw_result = RunResult(
                    tool=tool_name,
                    success=meta.get("success", True),
                    output_text=output_file.read_text(),
                )
                findings = parser.parse(raw_result)

                console.print(
                    f"  {tool_name} × {challenge_id} run {run_idx}: "
                    f"{len(findings)} findings"
                )

                # Heuristic matching
                heuristic_results = heuristic_match(challenge.issues, findings)

                # LLM judge (unless skipped)
                if skip_llm:
                    final_results = heuristic_results
                else:
                    final_results = llm_judge_batch(
                        challenge.issues, findings, heuristic_results, model=judge_model
                    )

                # Score
                scored = score_challenge_run(
                    challenge_id=challenge_id,
                    tool=tool_name,
                    run_index=run_idx,
                    num_findings=len(findings),
                    match_results=final_results,
                )
                all_results.append(scored)

                # Save evaluation
                eval_file = run_dir_path / "evaluation.json"
                eval_file.write_text(json.dumps(scored.model_dump(), indent=2))

    # Aggregate
    report = aggregate_results(
        all_results,
        judge_model=judge_model,
        tool_model=tool_model,
    )

    report_file = run_path / "report.json"
    report_file.write_text(json.dumps(report.model_dump(), indent=2))

    console.print(f"\n[green]Evaluation complete.[/green] Report: {report_file}")

    # Print summary
    for tool in report.tools:
        console.print(
            f"  {tool.tool}: F1={tool.mean_f1:.2%} "
            f"P={tool.mean_precision:.2%} R={tool.mean_recall:.2%}"
        )
