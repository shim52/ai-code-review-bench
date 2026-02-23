"""Abstract base for LLM-based code reviewers.

Provides the shared system prompt, diff/prompt-building logic, and a template
method ``run()`` so that concrete subclasses only need to implement the
API-specific ``_call_llm()`` and ``_resolve_model()`` methods.
"""

from __future__ import annotations

import os
import subprocess
from abc import abstractmethod
from pathlib import Path

from code_review_benchmark.runners.base import AbstractToolRunner, RunResult

CODE_REVIEW_SYSTEM_PROMPT = """\
You are an expert code reviewer. You will receive a git diff representing changes \
in a pull request. Analyze the diff carefully and identify all issues, bugs, \
security vulnerabilities, performance problems, and other concerns.

For each finding, output it in this exact format:

### Finding N
- **File**: <file path>
- **Lines**: <start_line>-<end_line> (or just <line> if single line)
- **Severity**: <critical|high|medium|low|info>
- **Category**: <security|bug|performance|error-handling|type-safety|style|other>
- **Title**: <short title>
- **Description**: <detailed explanation of the issue and why it matters>

Focus on:
- Security vulnerabilities (injection, XSS, CSRF, etc.)
- Bugs and logic errors
- Missing error handling
- Performance issues (N+1 queries, memory leaks, etc.)
- Race conditions
- Type safety issues
- Information disclosure

Do NOT report:
- Style preferences or formatting
- Missing documentation (unless it hides a real issue)
- Minor naming suggestions

If there are no significant issues, output:
### No Issues Found
"""


class AbstractLLMReviewer(AbstractToolRunner):
    """Intermediate base for reviewers that call an LLM with a diff."""

    # -- helpers used by run() ------------------------------------------------

    @staticmethod
    def _get_pr_title(repo_path: Path, pr_branch: str) -> str:
        try:
            proc = subprocess.run(
                ["git", "log", pr_branch, "--format=%s", "-1"],
                capture_output=True,
                text=True,
                timeout=10,
                cwd=repo_path,
            )
            return proc.stdout.strip()
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return ""

    @staticmethod
    def _get_diff(repo_path: Path, pr_branch: str, main_branch: str) -> str | None:
        try:
            proc = subprocess.run(
                ["git", "diff", f"{main_branch}...{pr_branch}"],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=repo_path,
            )
            return proc.stdout
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return None

    @staticmethod
    def _build_user_prompt(pr_title: str, diff_text: str) -> str:
        prompt = f"Pull request: {pr_title}\n\n" if pr_title else ""
        prompt += f"Please review the following diff:\n\n```diff\n{diff_text}\n```"
        return prompt

    # -- abstract hooks subclasses must provide --------------------------------

    @abstractmethod
    def _resolve_model(self, model: str | None) -> str:
        """Return the concrete model identifier to use."""

    @abstractmethod
    def _call_llm(
        self,
        system_prompt: str,
        user_prompt: str,
        model: str,
        timeout: int,
    ) -> str:
        """Send *system_prompt* and *user_prompt* to the LLM and return the response text."""

    # -- template method -------------------------------------------------------

    def run(
        self,
        repo_path: Path,
        pr_branch: str,
        main_branch: str,
        model: str | None = None,
    ) -> RunResult:
        resolved_model = self._resolve_model(model)

        pr_title = self._get_pr_title(repo_path, pr_branch)

        diff_text = self._get_diff(repo_path, pr_branch, main_branch)
        if diff_text is None:
            return RunResult(tool=self.name, success=False, error="Failed to get diff")
        if not diff_text.strip():
            return RunResult(tool=self.name, success=False, error="Empty diff")

        user_prompt = self._build_user_prompt(pr_title, diff_text)

        timeout = int(os.environ.get("CRB_TOOL_TIMEOUT", "300"))
        try:
            output_text = self._call_llm(
                system_prompt=CODE_REVIEW_SYSTEM_PROMPT,
                user_prompt=user_prompt,
                model=resolved_model,
                timeout=timeout,
            )
        except Exception as exc:
            return RunResult(tool=self.name, success=False, error=str(exc))

        has_review = bool(output_text and output_text.strip())
        return RunResult(
            tool=self.name,
            success=has_review,
            output_text=output_text,
        )
