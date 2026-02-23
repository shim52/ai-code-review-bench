"""Claude AI code reviewer — uses Claude models via Anthropic API or AWS Bedrock."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from code_review_benchmark.runners.base import AbstractToolRunner, RunResult
from code_review_benchmark.runners.registry import register_tool

DEFAULT_MODEL = "claude-opus-4-20250514"

# Map Anthropic model names to Bedrock model IDs.
_BEDROCK_MODEL_MAP = {
    "claude-opus-4-20250514": "us.anthropic.claude-opus-4-20250514-v1:0",
    "claude-sonnet-4-20250514": "us.anthropic.claude-sonnet-4-20250514-v1:0",
}

_SYSTEM_PROMPT = """\
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


@register_tool
class ClaudeReviewerRunner(AbstractToolRunner):
    @property
    def name(self) -> str:
        return "claude-reviewer"

    @property
    def version_command(self) -> list[str]:
        return ["python3", "-c", "import anthropic; print(anthropic.__version__)"]

    def is_available(self) -> bool:
        try:
            import anthropic  # noqa: F401
        except ImportError:
            return False
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        use_bedrock = os.environ.get("CRB_CLAUDE_USE_BEDROCK", "").lower() == "true"
        return bool(api_key or use_bedrock)

    def _resolve_model(self, model: str | None) -> str:
        """Determine which Claude model to use."""
        env_model = os.environ.get("CRB_CLAUDE_MODEL")
        if env_model:
            return env_model
        if model and ("claude" in model.lower() or "anthropic" in model.lower()):
            return model
        return DEFAULT_MODEL

    def _get_client(self):
        """Create the appropriate Anthropic client (direct API or Bedrock)."""
        import anthropic

        use_bedrock = os.environ.get("CRB_CLAUDE_USE_BEDROCK", "").lower() == "true"
        if use_bedrock:
            region = os.environ.get("AWS_REGION", os.environ.get("AWS_DEFAULT_REGION", "us-east-1"))
            return anthropic.AnthropicBedrock(aws_region=region), True
        return anthropic.Anthropic(), False

    def _bedrock_model_id(self, model: str) -> str:
        """Map an Anthropic model name to a Bedrock model ID if needed."""
        return _BEDROCK_MODEL_MAP.get(model, model)

    def run(
        self,
        repo_path: Path,
        pr_branch: str,
        main_branch: str,
        model: str | None = None,
    ) -> RunResult:
        resolved_model = self._resolve_model(model)

        # Get the PR commit message for context.
        try:
            title_proc = subprocess.run(
                ["git", "log", pr_branch, "--format=%s", "-1"],
                capture_output=True,
                text=True,
                timeout=10,
                cwd=repo_path,
            )
            pr_title = title_proc.stdout.strip()
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pr_title = ""

        # Generate the diff between main and PR branch.
        try:
            diff_proc = subprocess.run(
                ["git", "diff", f"{main_branch}...{pr_branch}"],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=repo_path,
            )
            diff_text = diff_proc.stdout
        except (subprocess.TimeoutExpired, FileNotFoundError) as exc:
            return RunResult(tool=self.name, success=False, error=f"Failed to get diff: {exc}")

        if not diff_text.strip():
            return RunResult(tool=self.name, success=False, error="Empty diff")

        # Build the user prompt.
        user_prompt = f"Pull request: {pr_title}\n\n" if pr_title else ""
        user_prompt += f"Please review the following diff:\n\n```diff\n{diff_text}\n```"

        # Call Claude.
        try:
            client, is_bedrock = self._get_client()
            api_model = self._bedrock_model_id(resolved_model) if is_bedrock else resolved_model

            timeout = int(os.environ.get("CRB_TOOL_TIMEOUT", "300"))
            response = client.messages.create(
                model=api_model,
                max_tokens=4096,
                system=_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_prompt}],
                timeout=timeout,
            )
            output_text = response.content[0].text
        except Exception as exc:
            return RunResult(tool=self.name, success=False, error=str(exc))

        has_review = bool(output_text and output_text.strip())
        return RunResult(
            tool=self.name,
            success=has_review,
            output_text=output_text,
        )
