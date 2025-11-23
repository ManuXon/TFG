# services/backend/src/openai/llm_client.py
import os
from functools import lru_cache
from typing import Optional, Dict, Any

from openai import OpenAI

# Default model if not overridden by env
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")


@lru_cache()
def get_openai_client() -> OpenAI:
    """
    Singleton-style OpenAI client.

    Reads API key from env and fails loudly if missing.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is not set. "
            "Pass it via environment variables / docker-compose."
        )
    return OpenAI(api_key=api_key)


def call_llm_json(
    system_prompt: str,
    user_prompt: str,
    model: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Call OpenAI chat completions and force JSON output.
    """
    client = get_openai_client()
    model_name = model or OPENAI_MODEL

    resp = client.chat.completions.create(
        model=model_name,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.0,
        max_tokens=512,
    )

    content = resp.choices[0].message.content
    if not content:
        raise RuntimeError("Empty response from LLM.")

    import json
    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"LLM did not return valid JSON: {content}") from e
