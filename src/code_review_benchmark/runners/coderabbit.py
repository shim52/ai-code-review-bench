"""CodeRabbit CLI runner.

Uses the official CodeRabbit CLI (https://docs.coderabbit.ai/cli).
Requires authentication via `coderabbit auth login` before use.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from code_review_benchmark.runners.base import AbstractToolRunner, RunResult
from code_review_benchmark.runners.registry import register_tool


@register_tool
class CodeRabbitRunner(AbstractToolRunner):
    @property
    def name(self) -> str:
        return "coderabbit"

    @property
    def version_command(self) -> list[str]:
        return ["coderabbit", "review", "--version"]

    def is_available(self) -> bool:
        try:
            result = subprocess.run(
                ["coderabbit", "review", "--version"],
                capture_output=True,
                timeout=15,
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def run(
        self,
        repo_path: Path,
        pr_branch: str,
        main_branch: str,
        model: str | None = None,
    ) -> RunResult:
        # CodeRabbit CLI reviews the current branch against --base.
        # We need to checkout the PR branch first so it sees the changes.
        try:
            subprocess.run(
                ["git", "checkout", pr_branch],
                capture_output=True,
                timeout=10,
                cwd=repo_path,
            )
        except subprocess.TimeoutExpired:
            return RunResult(
                tool=self.name, success=False, error="git checkout timed out"
            )

        cmd = [
            "coderabbit",
            "review",
            "--plain",
            "--base",
            main_branch,
            "--cwd",
            str(repo_path),
            "--no-color",
        ]

        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
                cwd=repo_path,
            )
        except subprocess.TimeoutExpired:
            return RunResult(
                tool=self.name, success=False, error="Timed out after 300s"
            )
        except FileNotFoundError:
            return RunResult(
                tool=self.name,
                success=False,
                error="coderabbit CLI not found. Install: curl -fsSL https://cli.coderabbit.ai/install.sh | sh",
            )

        return RunResult(
            tool=self.name,
            success=proc.returncode == 0,
            output_text=proc.stdout,
            error=proc.stderr,
            return_code=proc.returncode,
        )
