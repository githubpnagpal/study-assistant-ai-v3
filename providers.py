"""
AI Provider abstraction — supports Claude (Anthropic) and Groq (free).
Add new providers here without touching main.py.
"""

import os
import anthropic
from openai import OpenAI

PROVIDERS = {
    "1": {
        "name": "Claude Haiku 4.5",
        "provider": "claude",
        "model": "claude-haiku-4-5",
        "description": "Fast & cheap — great for study Q&A",
        "cost": "$1/$5 per 1M tokens",
    },
    "2": {
        "name": "Claude Sonnet 4.6",
        "provider": "claude",
        "model": "claude-sonnet-4-6",
        "description": "Smarter, with web search support",
        "cost": "$3/$15 per 1M tokens",
    },
    "3": {
        "name": "Groq — Llama 3.3 70B (FREE)",
        "provider": "groq",
        "model": "llama-3.3-70b-versatile",
        "description": "Free, very fast — great backup when Claude runs out",
        "cost": "FREE (rate limited)",
    },
    "4": {
        "name": "Groq — Llama 3.1 8B (FREE)",
        "provider": "groq",
        "model": "llama-3.1-8b-instant",
        "description": "Fastest free option — good for quick Q&A",
        "cost": "FREE (rate limited)",
    },
}


def get_claude_client() -> anthropic.Anthropic | None:
    key = os.getenv("ANTHROPIC_API_KEY")
    if not key:
        return None
    return anthropic.Anthropic(api_key=key)


def get_groq_client() -> OpenAI | None:
    key = os.getenv("GROQ_API_KEY")
    if not key:
        return None
    return OpenAI(api_key=key, base_url="https://api.groq.com/openai/v1")


def stream_claude(client: anthropic.Anthropic, model: str, messages: list, system: str) -> tuple[str, list]:
    """Stream a response from Claude and return (text, content_blocks)."""
    from tools import ALL_TOOLS
    full_text = ""

    with client.messages.stream(
        model=model,
        max_tokens=1024,
        system=system,
        tools=ALL_TOOLS,
        messages=messages,
    ) as stream:
        for event in stream:
            if event.type == "content_block_delta":
                if event.delta.type == "text_delta":
                    print(event.delta.text, end="", flush=True)
                    full_text += event.delta.text

        print()
        final = stream.get_final_message()
        return full_text, final.content


def stream_groq(client: OpenAI, model: str, messages: list, system: str) -> tuple[str, list]:
    """Stream a response from Groq and return (text, content_blocks)."""
    full_text = ""

    # Convert messages to OpenAI format (Groq is OpenAI-compatible)
    openai_messages = [{"role": "system", "content": system}] + [
        {
            "role": m["role"],
            "content": m["content"] if isinstance(m["content"], str) else str(m["content"])
        }
        for m in messages
    ]

    stream = client.chat.completions.create(
        model=model,
        messages=openai_messages,
        stream=True,
        max_tokens=1024,
    )

    for chunk in stream:
        delta = chunk.choices[0].delta.content or ""
        print(delta, end="", flush=True)
        full_text += delta

    print()
    return full_text, [{"type": "text", "text": full_text}]
