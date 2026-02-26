"""OpenAI code reviewer — uses OpenAI models (GPT-4o, etc.) via the OpenAI API."""

from __future__ import annotations

import os

from code_review_benchmark.runners.llm_reviewer_base import AbstractLLMReviewer
from code_review_benchmark.runners.registry import register_tool

DEFAULT_MODEL = "gpt-4o"


@register_tool
class OpenAIReviewerRunner(AbstractLLMReviewer):
    @property
    def name(self) -> str:
        return "openai-reviewer"

    @property
    def version_command(self) -> list[str]:
        return ["python3", "-c", "import openai; print(openai.__version__)"]

    def is_available(self) -> bool:
        try:
            import openai  # noqa: F401
        except ImportError:
            return False
        return bool(os.environ.get("OPENAI_API_KEY", ""))

    def _resolve_model(self, model: str | None) -> str:
        """Determine which OpenAI model to use."""
        env_model = os.environ.get("CRB_OPENAI_MODEL")
        if env_model:
            return env_model
        if model and ("gpt" in model.lower() or "openai" in model.lower() or "o1" in model.lower()):
            return model
        return DEFAULT_MODEL

    def _call_llm(
        self,
        system_prompt: str,
        user_prompt: str,
        model: str,
        timeout: int,
    ) -> str:
        from openai import OpenAI

        client = OpenAI()
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            timeout=timeout,
        )
        return response.choices[0].message.content or ""
