"""check_day (team tool, Lab 5): the date rules from day_points(), read-only, offered to everyone."""
import json
from datetime import date

import pytest
from pydantic import ValidationError

from src.act import call_tool
from src.contracts import CheckDay
from src.reserve import Event, day_points, demand_score
from src.tools import check_day, tools_for


def ask(caller=None, **arguments):
    return call_tool({"id": "c1", "name": "check_day", "arguments": json.dumps(arguments)}, tools_for(caller), caller)


@pytest.mark.parametrize("day, points, holiday, eve", [
    ("2026-10-23", 18, False, False),   # a Friday
    ("2026-05-12", 12, True, False),    # a holiday on a Tuesday
    ("2026-05-11", 12, False, True),    # the eve of that holiday
    ("2026-04-12", 27, True, True),     # Easter Sunday: a Sunday, a holiday and the eve of Easter Monday
    ("2026-11-30", 0, False, False),    # an ordinary Monday adds nothing
])
def test_points_and_flags(day, points, holiday, eve):
    r = check_day(CheckDay(day=day))
    assert (r.day_points, r.is_holiday, r.is_holiday_eve) == (points, holiday, eve)


def test_agrees_with_the_scoring_rules():
    """The tool and decide() share day_points(): a tier 3 event with nothing sold scores only its date."""
    for d in ("2026-10-23", "2026-05-11", "2026-04-12", "2026-11-30"):
        day = date.fromisoformat(d)
        score, _ = demand_score(Event("e", "football", 3, day, 1000, 0, 30))
        assert check_day(CheckDay(day=day)).day_points == score == day_points(day)[0]


def test_offered_to_an_anonymous_caller_and_runs():
    out = ask(day="2026-10-23")
    assert out["ok"] and out["result"]["weekday"] == "Friday" and out["result"]["reasons"] == ["Friday is a busy day (+18)"]


def test_same_call_twice_gives_the_same_answer():
    assert ask(day="2026-05-12")["result"] == ask(day="2026-05-12")["result"]


@pytest.mark.parametrize("bad", [{"day": "2027-03-03"}, {"day": "12 May"}, {"day": "2026-02-30"}, {}])
def test_invalid_dates_never_reach_the_tool(bad):
    out = ask(**bad)
    assert not out["ok"] and out["error"].startswith("invalid arguments: day")


def test_model_cannot_add_its_own_holidays_or_an_identity():
    for extra in ({"holidays": ["2026-11-30"]}, {"operator_id": "admin"}):
        out = ask(day="2026-11-30", **extra)
        assert not out["ok"] and "Extra inputs are not permitted" in out["error"]
    with pytest.raises(ValidationError):
        CheckDay(day="2026-11-30", is_holiday=True)
