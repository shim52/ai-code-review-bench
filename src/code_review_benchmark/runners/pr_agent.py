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
        return ["pr-agent", "--help"]

    def is_available(self) -> bool:
        try:
            subprocess.run(
                ["pr-agent", "--help"],
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

        # PR-Agent's handle_request calls apply_repo_settings() before parsing
        # CLI config overrides, so we must set the git provider via env vars
        # to ensure the local provider is selected before URL-based detection.
        env["CONFIG.GIT_PROVIDER"] = "local"
        if model:
            env["CONFIG.MODEL"] = model

        # Ensure HEAD is on the PR branch (the "source" branch).
        # LocalGitProvider reads head_branch_name from repo.head.ref.name.
        subprocess.run(
            ["git", "checkout", pr_branch],
            capture_output=True,
            timeout=10,
            cwd=repo_path,
        )

        # In local mode, LocalGitProvider.__init__(target_branch_name) is called
        # with pr_url as the first argument. It uses _find_repository_root() from
        # cwd to locate the repo, and treats pr_url as the TARGET (base) branch
        # name to diff against. So we pass main_branch here, not the repo path.
        cmd = [
            "pr-agent",
            f"--pr_url={main_branch}",
            "review",
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

        output_text = proc.stdout
        output_files: list[Path] = []
        review_md = repo_path / "review.md"
        if review_md.exists():
            output_text = review_md.read_text()
            output_files.append(review_md)

        has_review = bool(output_text and output_text.strip())
        stderr = proc.stderr or ""
        has_fatal = "Traceback (most recent call last)" in stderr or "| ERROR" in stderr
        success = proc.returncode == 0 and has_review and not has_fatal

        return RunResult(
            tool=self.name,
            success=success,
            output_text=output_text,
            output_files=output_files,
            error=proc.stderr,
            return_code=proc.returncode,
        )
