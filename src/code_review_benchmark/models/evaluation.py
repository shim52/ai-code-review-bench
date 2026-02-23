"""Evaluation result models."""

from __future__ import annotations

from pydantic import BaseModel, Field


class MatchResult(BaseModel):
    ground_truth_id: str
    finding_index: int | None = None  # index into the tool's findings list
    matched: bool = False
    match_score: float = 0.0  # 0-1 confidence
    match_method: str = ""  # "heuristic", "llm_judge", or "both"
    explanation: str = ""


class ChallengeToolResult(BaseModel):
    challenge_id: str
    tool: str
    run_index: int = 0
    findings: int = 0
    matches: list[MatchResult] = Field(default_factory=list)
    precision: float = 0.0
    recall: float = 0.0
    f1: float = 0.0


class ToolScore(BaseModel):
    tool: str
    challenges_run: int = 0
    total_ground_truths: int = 0
    total_findings: int = 0
    total_matched: int = 0
    mean_precision: float = 0.0
    mean_recall: float = 0.0
    mean_f1: float = 0.0
    stddev_precision: float = 0.0
    stddev_recall: float = 0.0
    stddev_f1: float = 0.0
    per_challenge: list[ChallengeToolResult] = Field(default_factory=list)
    metrics_breakdown: MetricsBreakdown | None = None


class CategoryMetrics(BaseModel):
    """Metrics for a specific category, severity, or language."""
    name: str
    total_ground_truths: int = 0
    total_findings: int = 0
    total_matched: int = 0
    precision: float = 0.0
    recall: float = 0.0
    f1: float = 0.0
    challenges_count: int = 0


class MetricsBreakdown(BaseModel):
    """Breakdown of metrics by different dimensions."""
    by_category: list[CategoryMetrics] = Field(default_factory=list)
    by_severity: list[CategoryMetrics] = Field(default_factory=list)
    by_language: list[CategoryMetrics] = Field(default_factory=list)


class BenchmarkReport(BaseModel):
    timestamp: str
    judge_model: str = ""
    tool_model: str = ""
    num_runs: int = 1
    challenges: list[str] = Field(default_factory=list)
    tools: list[ToolScore] = Field(default_factory=list)
    metrics_breakdown: MetricsBreakdown | None = None
