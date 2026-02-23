"""Abstract base class for tool runners.

This module defines the interface that all AI code review tool runners must implement.
Each tool runner is responsible for executing a specific tool against a git repository
and returning the raw output in a standardized format.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path


@dataclass
class RunResult:
    """Raw output from a tool run."""

    tool: str
    success: bool
    output_text: str = ""
    output_files: list[Path] | None = None
    error: str = ""
    return_code: int = 0


class AbstractToolRunner(ABC):
    """Interface every tool runner must implement."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Tool identifier (e.g. 'pr-agent')."""

    @property
    @abstractmethod
    def version_command(self) -> list[str]:
        """Command to check the tool's version."""

    @abstractmethod
    def is_available(self) -> bool:
        """Return True if the tool is installed and usable."""

    @abstractmethod
    def run(
        self,
        repo_path: Path,
        pr_branch: str,
        main_branch: str,
        model: str | None = None,
    ) -> RunResult:
        """Execute the tool against the repo and return raw output.

        Args:
            repo_path: Path to the git repository
            pr_branch: Name of the branch containing changes to review
            main_branch: Name of the base branch (typically 'main')
            model: Optional AI model to use (tool-specific)

        Returns:
            RunResult containing the tool's output and execution status

        Raises:
            NotImplementedError: Must be implemented by subclasses
        """
