from datetime import date

from src import llm
from src.reason import explain, facts, is_grounded, main, template
from src.reserve import Event, decide

BIG = decide(Event("ucl", "football", 1, date(2026, 10, 23), 50000, 85, 21))   # RESERVE 78, 5000
SMALL = decide(Event("loc", "football", 3, date(2026, 10, 27), 8000, 30, 20))  # SKIP


def fake_chat(reply):
    calls = []
    def chat(system, user, feature, **kw):
        calls.append((system, user, feature))
        return reply, {}
    chat.calls = calls
    return chat


def test_grounded_model_sentence_is_used():
    chat = fake_chat("Hold 5,000 seats: a tier 1 Friday match that is 85% sold 21 days out (score 78).")
    sentence, source = explain(BIG, chat=chat)
    assert source == "model" and sentence.startswith("Hold 5,000")
    system, user, feature = chat.calls[0]
    assert feature == "operator_reason" and "reason: tier 1 event (+35)" in user


def test_invented_number_falls_back_to_template():
    sentence, source = explain(BIG, chat=fake_chat("Hold 5,000 seats; demand is up 40% on last season."))
    assert source == "template:ungrounded" and sentence == template(BIG)


def test_rambling_answer_falls_back():
    assert not is_grounded("word " * 50, BIG)
    assert not is_grounded("line one\nline two", BIG)
    assert not is_grounded("", BIG)


def test_no_model_call_for_skip_or_watch():
    chat = fake_chat("should never be used")
    sentence, source = explain(SMALL, chat=chat)
    assert source == "template" and chat.calls == []


def test_no_key_still_gives_the_operator_a_reason(monkeypatch):
    monkeypatch.setattr(llm, "_client", None)
    sentence, source = explain(BIG, chat=llm.chat)
    assert source.startswith("template:no-model") and "5,000 seats (score 78)" in sentence


def test_facts_are_only_the_decision():
    assert facts(BIG).splitlines()[:3] == ["decision: RESERVE", "demand score: 78 of 100", "seats to hold: 5000"]


def test_cli_without_key(capsys, monkeypatch):
    monkeypatch.setattr(llm, "_client", None)
    assert main(["--tier", "1", "--day", "2026-10-23", "--capacity", "50000", "--sold", "85", "--days-out", "21"]) == 0
    out = capsys.readouterr().out
    assert "RESERVE score=78 seats=5000" in out and "reason [template:no-model" in out
