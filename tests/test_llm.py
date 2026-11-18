import json
from types import SimpleNamespace

import pytest

from src import llm


def fake_client(content="ok", prompt_tokens=600, completion_tokens=40, error=None):
    def create(**kw):
        if error:
            raise error
        fake_client.last_call = kw
        return SimpleNamespace(usage=SimpleNamespace(prompt_tokens=prompt_tokens, completion_tokens=completion_tokens),
                               choices=[SimpleNamespace(message=SimpleNamespace(content=content))])
    return SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))


def test_every_call_writes_one_usage_line(monkeypatch, usage_log):
    monkeypatch.setattr(llm, "client", lambda: fake_client("  Hold 5,000 seats.  "))
    text, usage = llm.chat("sys", "user", feature="operator_reason")
    assert text == "Hold 5,000 seats."
    lines = usage_log.read_text().splitlines()
    assert len(lines) == 1
    logged = json.loads(lines[0])
    assert set(logged) == {"ts", "feature", "model", "tokens_in", "tokens_out", "cost_usd", "latency_ms", "ok"}
    assert logged == usage
    assert (logged["feature"], logged["tokens_in"], logged["tokens_out"], logged["ok"]) == ("operator_reason", 600, 40, True)
    assert logged["cost_usd"] == pytest.approx((600 * 0.825 + 40 * 4.125) / 1e6)


def test_model_comes_from_environment(monkeypatch):
    monkeypatch.setenv("FANRESERVE_MODEL", "google/gemini-3.5-flash-lite")
    fc = fake_client()
    monkeypatch.setattr(llm, "client", lambda: fc)
    _, usage = llm.chat("s", "u", feature="t")
    assert fake_client.last_call["model"] == "google/gemini-3.5-flash-lite"
    assert fake_client.last_call["temperature"] == 0
    assert usage["cost_usd"] == pytest.approx((600 * 0.30 + 40 * 2.50) / 1e6)


def test_no_key_raises_without_network(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.setattr(llm, "_client", None)
    with pytest.raises(llm.LLMUnavailable, match="OPENROUTER_API_KEY"):
        llm.chat("s", "u", feature="t")


def test_provider_error_is_logged_and_wrapped(monkeypatch, usage_log):
    monkeypatch.setattr(llm, "client", lambda: fake_client(error=TimeoutError("slow")))
    with pytest.raises(llm.LLMUnavailable, match="TimeoutError"):
        llm.chat("s", "u", feature="t")
    logged = json.loads(usage_log.read_text())
    assert logged["ok"] is False and logged["tokens_in"] == 0


def test_unknown_model_costs_zero_not_crash():
    assert llm.cost_usd("someone/new-model", 1000, 1000) == 0.0
