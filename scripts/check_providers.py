#!/usr/bin/env python3
"""Quick diagnostic: verify all LLM provider credentials before running the benchmark."""

import os
import sys


def check_openai():
    key = os.environ.get("OPENAI_API_KEY", "")
    if not key:
        return "❌ OPENAI_API_KEY not set"
    try:
        from openai import OpenAI
        client = OpenAI()
        r = client.chat.completions.create(
            model="gpt-4o", messages=[{"role": "user", "content": "Say OK"}], max_tokens=5
        )
        return f"✅ OpenAI OK (model: gpt-4o, response: {r.choices[0].message.content.strip()})"
    except Exception as e:
        return f"❌ OpenAI error: {e}"


def check_anthropic():
    key = os.environ.get("ANTHROPIC_API_KEY", "")
    profile = os.environ.get("AWS_PROFILE", "")
    use_bedrock = os.environ.get("CRB_CLAUDE_USE_BEDROCK", "").lower() == "true"

    if not key and not profile and not use_bedrock:
        return "❌ No ANTHROPIC_API_KEY, AWS_PROFILE, or CRB_CLAUDE_USE_BEDROCK set"

    try:
        import anthropic

        if use_bedrock or (profile and not key):
            region = os.environ.get("AWS_REGION", os.environ.get("AWS_DEFAULT_REGION", "us-east-1"))
            client = anthropic.AnthropicBedrock(aws_region=region, aws_profile=profile or None)
            model = "us.anthropic.claude-sonnet-4-20250514-v1:0"
            mode = f"Bedrock (profile={profile or 'default'}, region={region})"
        else:
            client = anthropic.Anthropic()
            model = "claude-sonnet-4-20250514"
            mode = "Direct API"

        r = client.messages.create(
            model=model, max_tokens=5, messages=[{"role": "user", "content": "Say OK"}]
        )
        return f"✅ Anthropic OK via {mode} (response: {r.content[0].text.strip()})"
    except Exception as e:
        return f"❌ Anthropic error ({mode}): {e}"


def check_google():
    key = os.environ.get("GOOGLE_API_KEY", "")
    if not key:
        return "❌ GOOGLE_API_KEY not set"
    try:
        from google import genai
        client = genai.Client()
        r = client.models.generate_content(model="gemini-2.5-pro", contents="Say OK")
        return f"✅ Google OK (model: gemini-2.5-pro, response: {(r.text or '').strip()[:20]})"
    except Exception as e:
        return f"❌ Google error: {e}"


if __name__ == "__main__":
    print("=" * 60)
    print("🔍 Provider Credential Check")
    print("=" * 60)
    print()

    results = []
    for name, fn in [("OpenAI", check_openai), ("Anthropic/Bedrock", check_anthropic), ("Google Gemini", check_google)]:
        print(f"Checking {name}...", end=" ", flush=True)
        result = fn()
        print(result)
        results.append("❌" not in result)

    print()
    if all(results):
        print("🎉 All providers ready! You can run: crb run")
    else:
        print("⚠️  Fix the issues above before running the benchmark.")
        sys.exit(1)
