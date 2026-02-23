"""CodeRabbit local mode runner.

Since CodeRabbit primarily operates as a GitHub Action, this runner simulates
their review approach using OpenAI's API directly for local execution.
"""

from __future__ import annotations

import json
import os
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
        # CodeRabbit doesn't have a CLI, so we check for OpenAI API availability
        return ["python", "-c", "import openai; print(openai.__version__)"]

    def is_available(self) -> bool:
        """Check if OpenAI API is available for CodeRabbit simulation."""
        try:
            # Check if OpenAI Python package is installed
            subprocess.run(
                ["python", "-c", "import openai"],
                capture_output=True,
                timeout=5,
            )
            # Check if API key is set
            api_key = os.environ.get("OPENAI_API_KEY")
            return api_key is not None and len(api_key) > 0
        except (FileNotFoundError, subprocess.TimeoutExpired, subprocess.CalledProcessError):
            return False

    def run(
        self,
        repo_path: Path,
        pr_branch: str,
        main_branch: str,
        model: str | None = None,
    ) -> RunResult:
        """Run CodeRabbit-style review using OpenAI API.

        Since CodeRabbit doesn't have a standalone CLI, we simulate their
        review approach by generating a diff and calling OpenAI's API.
        """
        model = model or os.environ.get("OPENAI_MODEL", "gpt-4")

        try:
            # Generate diff between branches
            diff_cmd = ["git", "diff", f"{main_branch}...{pr_branch}"]
            diff_proc = subprocess.run(
                diff_cmd,
                capture_output=True,
                text=True,
                timeout=30,
                cwd=repo_path,
            )

            if diff_proc.returncode != 0:
                return RunResult(
                    tool=self.name,
                    success=False,
                    error=f"Failed to generate diff: {diff_proc.stderr}",
                )

            diff_content = diff_proc.stdout

            # Get list of changed files
            files_cmd = ["git", "diff", "--name-only", f"{main_branch}...{pr_branch}"]
            files_proc = subprocess.run(
                files_cmd,
                capture_output=True,
                text=True,
                timeout=30,
                cwd=repo_path,
            )

            changed_files = files_proc.stdout.strip().split("\n") if files_proc.stdout else []

            # Create the review using OpenAI API with CodeRabbit-style prompts
            review_script = f'''
import openai
import json
import sys

client = openai.OpenAI(api_key="{os.environ.get("OPENAI_API_KEY", "")}")

diff_content = """
{diff_content[:50000]}  # Limit diff size to avoid token limits
"""

changed_files = {changed_files}

# CodeRabbit-style system prompt
system_prompt = """You are CodeRabbit, an AI-powered code reviewer.
Review the following code changes and provide:
1. A summary of the changes
2. Line-by-line suggestions for improvements
3. Potential bugs or security issues
4. Code quality and best practice violations

Format your response in markdown with clear sections:
## Summary
## Issues Found
## Suggestions
## Line-by-Line Review

For each issue, specify:
- File path
- Line number(s)
- Severity (Critical/High/Medium/Low/Info)
- Description
- Suggested fix (if applicable)
"""

try:
    response = client.chat.completions.create(
        model="{model}",
        messages=[
            {{"role": "system", "content": system_prompt}},
            {{"role": "user", "content": f"Review this PR diff:\\n\\n{{diff_content}}"}}
        ],
        temperature=0.3,
        max_tokens=4000
    )

    review_content = response.choices[0].message.content
    print(review_content)
except Exception as e:
    print(f"Error: {{e}}", file=sys.stderr)
    sys.exit(1)
'''

            # Execute the review script
            review_proc = subprocess.run(
                ["python", "-c", review_script],
                capture_output=True,
                text=True,
                timeout=300,
                cwd=repo_path,
            )

            if review_proc.returncode != 0:
                return RunResult(
                    tool=self.name,
                    success=False,
                    error=f"Review failed: {review_proc.stderr}",
                )

            # Save the review output
            review_dir = repo_path / ".coderabbit"
            review_dir.mkdir(exist_ok=True)
            review_file = review_dir / "review.md"
            review_file.write_text(review_proc.stdout)

            return RunResult(
                tool=self.name,
                success=True,
                output_text=review_proc.stdout,
                output_files=[review_file],
                error=review_proc.stderr,
                return_code=review_proc.returncode,
            )

        except subprocess.TimeoutExpired:
            return RunResult(tool=self.name, success=False, error="Timed out after 300s")
        except Exception as e:
            return RunResult(tool=self.name, success=False, error=str(e))