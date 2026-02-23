"""Abstract base class for output parsers."""

from __future__ import annotations

from abc import ABC, abstractmethod

from code_review_benchmark.models.finding import NormalizedFinding
from code_review_benchmark.runners.base import RunResult


class AbstractOutputParser(ABC):
    """Parses raw tool output into normalized findings."""

    @property
    @abstractmethod
    def tool_name(self) -> str:
        """Which tool this parser handles."""

    @abstractmethod
    def parse(self, result: RunResult) -> list[NormalizedFinding]:
        """Convert a RunResult into a list of NormalizedFinding."""
