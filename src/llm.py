"""The only file that talks to a model (docs/decisions/0003): chat() and, from Week 5, complete_tools().

Every call writes one line to logs/usage.jsonl: time, feature, model, tokens,
cost and latency. The key comes from the environment (OPENROUTER_API_KEY),
never from a file in the repo. The client is built lazily, so importing this
module needs no key, and tests replace `client` with a fake.
"""
from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_MODEL = "google/gemini-3.8-flash"

# USD per million tokens (input, output), read from openrouter.ai/api/v1/models
# on 2026-11-18. Re-check before trusting the cost column.
PRICES = {
    "google/gemini-3.8-flash": (0.825, 4.125),
    "google/gemini-3.5-flash-lite": (0.30, 2.50),
}


class LLMUnavailable(RuntimeError):
    """No key, or the provider failed. Callers fall back to a non-model path."""


def model() -> str:
    return os.environ.get("FANRESERVE_MODEL", DEFAULT_MODEL)


def log_path() -> Path:
    return Path(os.environ.get("FANRESERVE_USAGE_LOG", "logs/usage.jsonl"))


_client = None


def client():
    global _client
    if _client is None:
        key = os.environ.get("OPENROUTER_API_KEY")
        if not key:
            raise LLMUnavailable("OPENROUTER_API_KEY is not set; export it in your shell")
        from openai import OpenAI  # imported here so tests and CI never need the package to reach the network

        _client = OpenAI(base_url=OPENROUTER_BASE_URL, api_key=key, timeout=20)
    return _client


def cost_usd(model_id: str, tokens_in: int, tokens_out: int) -> float:
    price_in, price_out = PRICES.get(model_id, (0.0, 0.0))
    return round((tokens_in * price_in + tokens_out * price_out) / 1_000_000, 8)


def log_usage(feature: str, model_id: str, tokens_in: int, tokens_out: int,
              latency_ms: int, ok: bool = True) -> dict:
    line = {
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "feature": feature,
        "model": model_id,
        "tokens_in": tokens_in,
        "tokens_out": tokens_out,
        "cost_usd": cost_usd(model_id, tokens_in, tokens_out),
        "latency_ms": latency_ms,
        "ok": ok,
    }
    path = log_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(line) + "\n")
    return line


def chat(system: str, user: str, feature: str, max_tokens: int = 120) -> tuple[str, dict]:
    """One chat completion. Returns (text, usage line). Raises LLMUnavailable."""
    model_id = model()
    started = time.perf_counter()
    try:
        resp = client().chat.completions.create(
            model=model_id,
            temperature=0,
            max_tokens=max_tokens,
            messages=[{"role": "system", "content": system},
                      {"role": "user", "content": user}],
        )
    except LLMUnavailable:
        raise
    except Exception as err:  # network, 401, 429, 5xx: log the failed call, then let the caller fall back
        log_usage(feature, model_id, 0, 0, round((time.perf_counter() - started) * 1000), ok=False)
        raise LLMUnavailable(f"model call failed: {type(err).__name__}: {err}") from err
    u = resp.usage
    usage = log_usage(feature, model_id, u.prompt_tokens or 0, u.completion_tokens or 0,
                      round((time.perf_counter() - started) * 1000))
    return (resp.choices[0].message.content or "").strip(), usage


def complete_tools(messages: list[dict], tools: list[dict], feature: str = "act",
                   max_tokens: int = 400) -> dict:
    """One model turn that may ask for tools (Week 5). Same client, same usage log.

    Returns {"content", "tool_calls": [{"id", "name", "arguments"}], "reasoning_details"}.
    The model only ASKS for a tool; src/act.py decides whether anything runs. Raises LLMUnavailable.
    """
    model_id = model()
    started = time.perf_counter()
    try:
        resp = client().chat.completions.create(
            model=model_id, temperature=0, max_tokens=max_tokens,
            messages=messages, tools=tools, tool_choice="auto",
        )
    except LLMUnavailable:
        raise
    except Exception as err:
        log_usage(feature, model_id, 0, 0, round((time.perf_counter() - started) * 1000), ok=False)
        raise LLMUnavailable(f"model call failed: {type(err).__name__}: {err}") from err
    u = resp.usage
    log_usage(feature, model_id, u.prompt_tokens or 0, u.completion_tokens or 0,
              round((time.perf_counter() - started) * 1000))
    m = resp.choices[0].message
    calls = [{"id": c.id, "name": c.function.name, "arguments": c.function.arguments or "{}"}
             for c in (m.tool_calls or [])]
    extra = getattr(m, "model_extra", None) or {}
    return {"content": m.content, "tool_calls": calls, "reasoning_details": extra.get("reasoning_details")}
