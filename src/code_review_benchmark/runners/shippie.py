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

        # Ensure we're on the PR branch.
        subprocess.run(
            ["git", "checkout", pr_branch],
            capture_output=True,
            timeout=10,
            cwd=repo_path,
        )

        # Shippie local mode hardcodes `git diff --cached` (staged changes only).
        # The challenge repo has changes committed, not staged. Soft-reset the
        # last commit so the diff appears as staged changes.
        subprocess.run(
            ["git", "reset", "--soft", "HEAD~1"],
            capture_output=True,
            timeout=10,
            cwd=repo_path,
        )

        cmd = [
            "npx",
            "shippie",
            "review",
            "--platform",
            "local",
        ]
        if model:
            # Shippie expects format "provider:model", e.g. "openai:gpt-5.2-2025-12-11"
            model_str = model if ":" in model else f"openai:{model}"
            cmd.extend(["--modelString", model_str])

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

        combined = (output_text or "") + (proc.stderr or "")
        has_review = bool(output_text and output_text.strip())
        no_changes = "no changes found" in combined.lower()
        success = proc.returncode == 0 and has_review and not no_changes

        return RunResult(
            tool=self.name,
            success=success,
            output_text=output_text,
            output_files=output_files,
            error=proc.stderr,
            return_code=proc.returncode,
        )
