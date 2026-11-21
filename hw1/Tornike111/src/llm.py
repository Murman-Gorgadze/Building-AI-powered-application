"""One door for every model call: logs tokens, cost and latency to a JSONL file.

The API key comes from the OPENROUTER_API_KEY environment variable, never a file.
Tests pass their own `transport`, so they never touch the network.
"""
from __future__ import annotations

import json
import os
import time
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path

URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = os.environ.get("HW1_MODEL", "google/gemini-2.5-flash")
# USD per million tokens for google/gemini-2.5-flash, from the OpenRouter models API on 21 Nov 2026.
PRICE_IN, PRICE_OUT = 0.30, 2.50
LOG_PATH = Path(os.environ.get("HW1_USAGE_LOG", Path(__file__).parent / "logs" / "usage.jsonl"))


@dataclass
class LLMResult:
    text: str
    model: str
    tokens_in: int
    tokens_out: int
    cost_usd: float
    latency_s: float


def _openrouter(payload: dict) -> dict:
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        raise RuntimeError("OPENROUTER_API_KEY is not set")
    req = urllib.request.Request(
        URL, data=json.dumps(payload).encode(),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


# Reasoning models spend output tokens "thinking" before the answer; with 120 they ran out
# (finish_reason: length, live run 21 Nov). This is a ceiling, not a charge.
MAX_TOKENS = 1000


def complete(prompt: str, *, model: str = DEFAULT_MODEL, max_tokens: int = MAX_TOKENS,
             transport=_openrouter, log_path: Path | None = None) -> LLMResult:
    payload = {"model": model, "max_tokens": max_tokens, "temperature": 0,
               "messages": [{"role": "user", "content": prompt}]}
    start = time.perf_counter()
    raw = transport(payload)
    latency = time.perf_counter() - start
    usage = raw.get("usage", {})
    t_in, t_out = usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0)
    choice = raw["choices"][0]
    # Reasoning models can spend every output token "thinking" and return content = None.
    content = choice["message"].get("content") or ""
    result = LLMResult(
        text=content.strip(),
        model=raw.get("model", model), tokens_in=t_in, tokens_out=t_out,
        cost_usd=0.0 if model.endswith(":free")  # OpenRouter free models cost nothing
        else round((t_in * PRICE_IN + t_out * PRICE_OUT) / 1_000_000, 8),
        latency_s=round(latency, 3))
    path = log_path or LOG_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as f:
        row = {k: v for k, v in asdict(result).items() if k != "text"}
        f.write(json.dumps({"ts": time.time(), **row}) + "\n")
    if not result.text:  # logged first: the tokens were used even with no answer
        raise RuntimeError(f"model returned no text (finish_reason: {choice.get('finish_reason')})")
    return result
