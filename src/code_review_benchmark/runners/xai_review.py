"""xai-review (AI Review) CLI runner."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from code_review_benchmark.runners.base import AbstractToolRunner, RunResult
from code_review_benchmark.runners.registry import register_tool


@register_tool
class XAIReviewRunner(AbstractToolRunner):
    @property
    def name(self) -> str:
        return "xai-review"

    @property
    def version_command(self) -> list[str]:
        return ["xai-review", "--version"]

    def is_available(self) -> bool:
        try:
            result = subprocess.run(
                ["xai-review", "--version"],
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
        env = {**os.environ}
        if model:
            env["OPENAI_MODEL"] = model

        cmd = [
            "xai-review",
            "review",
            "--repo-path",
            str(repo_path),
            "--base-branch",
            main_branch,
            "--target-branch",
            pr_branch,
        ]

        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
                cwd=repo_path,
                env=env,
            )
        except subprocess.TimeoutExpired:
            return RunResult(tool=self.name, success=False, error="Timed out after 300s")
        except FileNotFoundError:
            return RunResult(tool=self.name, success=False, error="xai-review not found")

        return RunResult(
            tool=self.name,
            success=proc.returncode == 0,
            output_text=proc.stdout,
            error=proc.stderr,
            return_code=proc.returncode,
        )
