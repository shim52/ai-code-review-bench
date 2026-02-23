"""The `crb report` command — generate comparison reports."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

console = Console()


def report_cmd(
    run_dir: str = typer.Option("results/latest", "--run-dir", help="Path to run results"),
    output_format: str = typer.Option(
        "markdown", "--format", help="Output format: markdown, json, both"
    ),
    output_file: Optional[str] = typer.Option(None, "--output", "-o", help="Output file path"),
) -> None:
    """Generate comparison reports from evaluated results."""
    from code_review_benchmark.models.evaluation import BenchmarkReport
    from code_review_benchmark.reports.json_report import generate_json_report
    from code_review_benchmark.reports.markdown import generate_markdown_report

    project_root = Path(__file__).resolve().parents[4]
    run_path = Path(run_dir) if Path(run_dir).is_absolute() else project_root / run_dir

    report_file = run_path / "report.json"
    if not report_file.exists():
        console.print(
            f"[red]No report.json found in {run_path}. Run `crb evaluate` first.[/red]"
        )
        raise typer.Exit(1)

    report = BenchmarkReport.model_validate(json.loads(report_file.read_text()))

    if output_format in ("markdown", "both"):
        md = generate_markdown_report(report)
        if output_file and output_format == "markdown":
            Path(output_file).write_text(md)
            console.print(f"Markdown report written to {output_file}")
        else:
            md_path = run_path / "report.md"
            md_path.write_text(md)
            console.print(f"Markdown report: {md_path}")
            console.print()
            console.print(md)

    if output_format in ("json", "both"):
        jr = generate_json_report(report)
        if output_file and output_format == "json":
            Path(output_file).write_text(jr)
            console.print(f"JSON report written to {output_file}")
        else:
            json_path = run_path / "report_formatted.json"
            json_path.write_text(jr)
            console.print(f"JSON report: {json_path}")
