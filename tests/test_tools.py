"""check_reserve: the contract refuses what decide() must never see; the tool only restates decide()."""
from datetime import date

import pytest
from pydantic import ValidationError

from src.contracts import CheckReserve
from src.reserve import Event, decide
from src.tools import TOOLS, ToolFailure, check_reserve, tools_for

GOOD = dict(tier=1, day="2026-10-23", capacity=50000, sold_pct=85, days_out=21)


def test_tool_returns_exactly_what_decide_returns():
    r = check_reserve(CheckReserve(**GOOD, event_id="ev-1"))
    d = decide(Event("ev-1", "football", 1, date(2026, 10, 23), 50000, 85, 21))
    assert (r.action, r.score, r.reserve_seats, r.reasons) == (d.action, d.score, d.reserve_seats, d.reasons)


def test_same_call_twice_gives_the_same_answer_and_changes_nothing():
    args = CheckReserve(**GOOD)
    assert check_reserve(args) == check_reserve(args)


@pytest.mark.parametrize("field, value", [
    ("tier", 0), ("tier", 4), ("capacity", 0), ("capacity", 10_000_000), ("sold_pct", -1), ("sold_pct", 150),
    ("days_out", -1), ("days_out", 400), ("day", "2027-01-01"), ("day", "2026-02-30"), ("category", "cricket"),
    ("event_id", "EV 1; DROP"), ("event_id", "x" * 40),
])
def test_contract_refuses_out_of_range(field, value):
    with pytest.raises(ValidationError) as e:
        CheckReserve(**{**GOOD, field: value})
    assert e.value.errors()[0]["loc"] == (field,)


def test_contract_refuses_fields_it_did_not_ask_for():
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        CheckReserve(**GOOD, reserve_seats=50000)


def test_contract_has_no_identity_field():
    fields = set(CheckReserve.model_fields)
    assert not fields & {"operator", "operator_id", "user", "user_id", "caller", "account", "fan_id"}


def test_backstop_turns_decide_errors_into_a_message_for_the_model(monkeypatch):
    monkeypatch.setattr("src.tools.decide", lambda e: (_ for _ in ()).throw(ValueError("tier must be 1..3, got 9")))
    with pytest.raises(ToolFailure, match="Fix that value and call check_reserve again"):
        check_reserve(CheckReserve(**GOOD))


def test_schema_the_model_sees_comes_from_the_contract():
    s = TOOLS["check_reserve"].schema()["function"]
    assert s["name"] == "check_reserve" and "Reads only" in s["description"]
    assert s["parameters"]["additionalProperties"] is False
    assert s["parameters"]["properties"]["sold_pct"]["maximum"] == 100


def test_check_reserve_is_offered_to_everyone_operator_only_tools_are_not():
    assert "check_reserve" in tools_for(None) and "check_reserve" in tools_for("op-1")
    assert all(not t.operator_only for t in tools_for(None).values())
