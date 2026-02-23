"""Claude AI code reviewer — uses Claude models via Anthropic API or AWS Bedrock."""

from __future__ import annotations

import os

from code_review_benchmark.runners.llm_reviewer_base import AbstractLLMReviewer
from code_review_benchmark.runners.registry import register_tool

DEFAULT_MODEL = "claude-opus-4-20250514"

# Map Anthropic model names to Bedrock model IDs.
_BEDROCK_MODEL_MAP = {
    "claude-opus-4-20250514": "us.anthropic.claude-opus-4-20250514-v1:0",
    "claude-sonnet-4-20250514": "us.anthropic.claude-sonnet-4-20250514-v1:0",
}


@register_tool
class ClaudeReviewerRunner(AbstractLLMReviewer):
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

    def _call_llm(
        self,
        system_prompt: str,
        user_prompt: str,
        model: str,
        timeout: int,
    ) -> str:
        client, is_bedrock = self._get_client()
        api_model = self._bedrock_model_id(model) if is_bedrock else model

        response = client.messages.create(
            model=api_model,
            max_tokens=4096,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
            timeout=timeout,
        )
        return response.content[0].text
