"""Normalized finding — common output format across all tools."""

from __future__ import annotations

from pydantic import BaseModel, Field

from code_review_benchmark.models.challenge import Severity


class NormalizedFinding(BaseModel):
    tool: str
    file: str | None = None
    line_start: int | None = None
    line_end: int | None = None
    severity: Severity | None = None
    category: str | None = None
    title: str = ""
    description: str = ""
    raw_text: str = ""
    keywords: list[str] = Field(default_factory=list)
