import sys
import pathlib

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import llm  # noqa: E402
from explain import explain, is_grounded  # noqa: E402

RESERVE = {"event_id": "ucl-1", "action": "RESERVE", "score": 78, "reserve_seats": 5000,
           "reasons": ["tier 1 event (+35)", "Friday is a busy day (+18)",
                       "selling fast, 85% sold 21d out (+25)"]}


def fake_model(reply):
    """A stand-in for llm.complete that records calls and never touches the network."""
    calls = []

    def call(prompt):
        calls.append(prompt)
        return llm.LLMResult(reply, "fake", 10, 5, 0.0, 0.0)
    call.calls = calls
    return call


# g1: a grounded model sentence is used as-is
def test_g1_grounded_sentence_is_used():
    call = fake_model("Hold 5,000 seats: tier 1 Friday match, 85% sold 21 days out.")
    out = explain(RESERVE, call=call)
    assert out.source == "model"
    assert out.text.startswith("Hold 5,000 seats")
    assert all(r in call.calls[0] for r in RESERVE["reasons"])


# g2: the model invents a price -> caught, operator gets the template instead
def test_g2_invented_number_falls_back():
    call = fake_model("Hold 5,000 seats; fans will pay 40 GEL each and it sells out in 2 hours.")
    out = explain(RESERVE, call=call)
    assert out.source == "fallback"
    assert "40" not in out.text and "tier 1 event (+35)" in out.text


# g3: SKIP / WATCH never call the model
@pytest.mark.parametrize("action", ["SKIP", "WATCH"])
def test_g3_non_reserve_makes_no_call(action):
    call = fake_model("should not be used")
    assert explain({**RESERVE, "action": action, "reserve_seats": 0}, call=call) is None
    assert call.calls == []


def test_model_error_falls_back():
    def broken(prompt):
        raise RuntimeError("OPENROUTER_API_KEY is not set")
    assert explain(RESERVE, call=broken).source == "fallback"


def test_too_long_sentence_is_rejected():
    assert not is_grounded("word " * 41, RESERVE)


@pytest.mark.parametrize("bad", [
    {k: v for k, v in RESERVE.items() if k != "reasons"},
    {**RESERVE, "reasons": []},
    {**RESERVE, "action": "MAYBE"},
])
def test_bad_decision_raises(bad):
    with pytest.raises(ValueError):
        explain(bad, call=fake_model("x"))


def test_llm_logs_usage(tmp_path):
    def transport(payload):
        return {"model": "fake/model", "usage": {"prompt_tokens": 600, "completion_tokens": 150},
                "choices": [{"message": {"content": " hi "}}]}
    log = tmp_path / "usage.jsonl"
    r = llm.complete("p", transport=transport, log_path=log)
    assert r.text == "hi" and r.tokens_in == 600
    assert r.cost_usd == pytest.approx((600 * 0.30 + 150 * 2.50) / 1e6)
    row = log.read_text().strip()
    assert '"tokens_out": 150' in row and "hi" not in row
