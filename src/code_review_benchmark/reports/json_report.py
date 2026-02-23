"""Generate machine-readable JSON reports."""

from __future__ import annotations

import json

from code_review_benchmark.models.evaluation import BenchmarkReport


def generate_json_report(report: BenchmarkReport) -> str:
    """Serialize a BenchmarkReport to formatted JSON."""
    return json.dumps(report.model_dump(), indent=2)
