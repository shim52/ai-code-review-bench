"""PR-Agent local mode runner."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from code_review_benchmark.runners.base import AbstractToolRunner, RunResult
from code_review_benchmark.runners.registry import register_tool


@register_tool
class PRAgentRunner(AbstractToolRunner):
    @property
    def name(self) -> str:
        return "pr-agent"

    @property
    def version_command(self) -> list[str]:
        return ["python", "-m", "pr_agent", "--version"]

    def is_available(self) -> bool:
        try:
            subprocess.run(
                ["python", "-m", "pr_agent", "--help"],
                capture_output=True,
                timeout=15,
            )
            return True
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

        # PR-Agent supports local git provider via --pr_url pointing to local path
        cmd = [
            "python",
            "-m",
            "pr_agent",
            "--pr_url",
            str(repo_path),
            "review",
            "--git_provider.git_provider=local",
            f"--local.branch={pr_branch}",
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
            return RunResult(tool=self.name, success=False, error="pr-agent not found")

        # PR-Agent writes review output to stdout and optionally to review.md
        output_text = proc.stdout
        output_files: list[Path] = []
        review_md = repo_path / "review.md"
        if review_md.exists():
            output_text = review_md.read_text()
            output_files.append(review_md)

        return RunResult(
            tool=self.name,
            success=proc.returncode == 0,
            output_text=output_text,
            output_files=output_files,
            error=proc.stderr,
            return_code=proc.returncode,
        )
