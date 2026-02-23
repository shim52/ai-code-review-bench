"""Shippie local platform runner."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from code_review_benchmark.runners.base import AbstractToolRunner, RunResult
from code_review_benchmark.runners.registry import register_tool


@register_tool
class ShippieRunner(AbstractToolRunner):
    @property
    def name(self) -> str:
        return "shippie"

    @property
    def version_command(self) -> list[str]:
        return ["npx", "shippie", "--version"]

    def is_available(self) -> bool:
        try:
            result = subprocess.run(
                ["npx", "shippie", "--version"],
                capture_output=True,
                timeout=30,
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
            "npx",
            "shippie",
            "--platform",
            "local",
            "--base-branch",
            main_branch,
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
            return RunResult(tool=self.name, success=False, error="npx/shippie not found")

        output_text = proc.stdout
        output_files: list[Path] = []

        # Shippie writes reviews to .shippie/review/
        review_dir = repo_path / ".shippie" / "review"
        if review_dir.exists():
            for md_file in sorted(review_dir.glob("*.md")):
                output_files.append(md_file)
                output_text += "\n" + md_file.read_text()

        return RunResult(
            tool=self.name,
            success=proc.returncode == 0,
            output_text=output_text,
            output_files=output_files,
            error=proc.stderr,
            return_code=proc.returncode,
        )
