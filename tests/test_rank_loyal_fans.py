"""rank_loyal_fans: operator-only, the caller comes from the app, every number bounded, no identity
in the arguments, and the result is exactly what rank_fans() says. Offline, no model."""
import asyncio
import json
from datetime import date

import pytest
from mcp import Client
from pydantic import ValidationError

from src import tools
from src.act import call_tool
from src.contracts import RankLoyalFans
from src.mcp_server import mcp
from src.reserve import rank_fans
from src.tools import TOOLS, ToolFailure, load_attendance, rank_loyal_fans, tools_for

GOOD = {"category": "football", "as_of": "2026-11-20"}


def call(**arguments):
    return {"id": "1", "name": "rank_loyal_fans", "arguments": json.dumps(arguments)}


def mcp_call(args):
    async def go():
        async with Client(mcp) as c:
            return await c.call_tool("rank_loyal_fans", args)
    return asyncio.run(go())


# ---------------------------------------------------------------- the tool restates rank_fans()

def test_result_is_exactly_what_rank_fans_returns():
    r = rank_loyal_fans(RankLoyalFans(**GOOD), caller="op-1")
    expected = rank_fans(load_attendance(), "football", date(2026, 11, 20))
    assert [(f.fan_id, f.visits) for f in r.fans] == expected
    assert (r.window_days, r.min_visits, r.total_loyal) == (90, 3, len(expected))


def test_window_edges_and_future_visits():
    concert = rank_loyal_fans(RankLoyalFans(category="concert", as_of="2026-11-20"), caller="op-1")
    ids = {f.fan_id for f in concert.fans}
    assert "fan-0009" in ids          # third visit is on 2026-08-22, the window's first day
    assert "fan-0010" not in ids      # third visit is on 2026-08-21, one day too early
    football = {f.fan_id for f in rank_loyal_fans(RankLoyalFans(**GOOD), caller="op-1").fans}
    assert not football & {"fan-0006", "fan-0016", "fan-0018"}   # too old, or one visit after as_of


def test_limit_cuts_the_list_but_not_the_count():
    r = rank_loyal_fans(RankLoyalFans(**GOOD, limit=2), caller="op-1")
    assert [f.fan_id for f in r.fans] == ["fan-0001", "fan-0002"] and r.total_loyal == 5


def test_same_call_twice_gives_the_same_answer_and_changes_nothing():
    before = tools.ATTENDANCE_PATH.read_bytes()
    args = RankLoyalFans(**GOOD)
    assert rank_loyal_fans(args, caller="op-1") == rank_loyal_fans(args, caller="op-1")
    assert tools.ATTENDANCE_PATH.read_bytes() == before


def test_no_loyal_fans_is_a_message_for_the_model():
    with pytest.raises(ToolFailure, match="no loyal theatre fans.*do not lower the bar or invent fan ids"):
        rank_loyal_fans(RankLoyalFans(category="theatre", as_of="2026-11-20"), caller="op-1")


@pytest.mark.parametrize("content", [None, "not json", '{"fans": {"fan-0001": [["football", "yesterday"]]}}'])
def test_missing_or_broken_data_leaks_no_path(tmp_path, monkeypatch, content):
    path = tmp_path / "attendance.json"
    if content is not None:
        path.write_text(content, encoding="utf-8")
    monkeypatch.setattr(tools, "ATTENDANCE_PATH", path)
    with pytest.raises(ToolFailure) as e:
        rank_loyal_fans(RankLoyalFans(**GOOD), caller="op-1")
    msg = str(e.value)
    assert "not available" in msg and "attendance.json" not in msg and str(tmp_path) not in msg


# ---------------------------------------------------------------- the contract

@pytest.mark.parametrize("field, value", [
    ("limit", 0), ("limit", 51), ("limit", 10_000), ("as_of", "2025-12-31"), ("as_of", "2027-01-01"),
    ("as_of", "2026-02-30"), ("as_of", "today"), ("category", "cricket"), ("category", "football; DROP"),
])
def test_contract_refuses_out_of_range(field, value):
    with pytest.raises(ValidationError) as e:
        RankLoyalFans(**{**GOOD, field: value})
    assert e.value.errors()[0]["loc"] == (field,)


def test_category_and_as_of_are_required():
    with pytest.raises(ValidationError):
        RankLoyalFans(category="football")
    with pytest.raises(ValidationError):
        RankLoyalFans(as_of="2026-11-20")


@pytest.mark.parametrize("extra", [{"operator_id": "admin"}, {"fan_id": "fan-0006"},
                                   {"min_visits": 1}, {"window_days": 3650}])
def test_contract_refuses_identity_and_rule_changes(extra):
    """No one in the arguments, and the loyalty rule cannot be loosened by the model."""
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        RankLoyalFans(**GOOD, **extra)


def test_contract_has_no_identity_field():
    assert not set(RankLoyalFans.model_fields) & {"operator", "operator_id", "user", "user_id", "caller",
                                                   "account", "fan_id", "fan"}


def test_schema_the_model_sees_comes_from_the_contract():
    s = TOOLS["rank_loyal_fans"].schema()["function"]
    assert "Operators only" in s["description"] and "Reads only" in s["description"]
    assert s["parameters"]["additionalProperties"] is False
    assert s["parameters"]["properties"]["limit"]["maximum"] == 50


# ---------------------------------------------------------------- who may call it (function-calling door)

def test_offered_to_operators_only():
    assert "rank_loyal_fans" not in tools_for(None)
    assert "rank_loyal_fans" in tools_for("op-1")
    assert TOOLS["rank_loyal_fans"].operator_only and TOOLS["rank_loyal_fans"].needs_caller


def test_anonymous_caller_never_reaches_the_data(monkeypatch):
    monkeypatch.setattr(tools, "load_attendance", lambda: pytest.fail("anonymous call read fan data"))
    out = call_tool(call(**GOOD), tools_for(None), None)
    assert not out["ok"] and "no tool named 'rank_loyal_fans'" in out["error"]


def test_backstop_refuses_without_a_caller_even_if_registered_wrongly():
    with pytest.raises(ToolFailure, match="signed-in operators only"):
        rank_loyal_fans(RankLoyalFans(**GOOD), caller=None)


def test_model_cannot_choose_the_caller():
    out = call_tool(call(**GOOD, operator_id="admin"), tools_for("op-1"), "op-1")
    assert not out["ok"] and "operator_id: Extra inputs are not permitted" in out["error"]


def test_operator_call_runs_and_logs_a_hashed_caller_but_no_fan_data(tool_log):
    out = call_tool(call(**GOOD), tools_for("op-1"), "op-1")
    assert out["ok"] and out["result"]["fans"][0] == {"fan_id": "fan-0001", "visits": 6}
    line = json.loads(tool_log.read_text(encoding="utf-8").splitlines()[-1])
    assert line["tool"] == "rank_loyal_fans" and line["ok"] and line["caller"] == tools.caller_key("op-1")
    assert "op-1" not in json.dumps(line) and "fan-0001" not in json.dumps(line)


# ---------------------------------------------------------------- the MCP door

def test_mcp_refuses_when_nobody_is_signed_in():
    r = mcp_call(GOOD)
    assert r.is_error and "Not signed in" in r.content[0].text


def test_mcp_signed_in_operator_gets_the_ranking(monkeypatch):
    monkeypatch.setenv("FANRESERVE_OPERATOR", "op-1")
    r = mcp_call(GOOD)
    assert not r.is_error and r.structured_content["total_loyal"] == 5


def test_mcp_refuses_an_operator_id_in_the_arguments(monkeypatch):
    monkeypatch.setenv("FANRESERVE_OPERATOR", "op-1")
    r = mcp_call({**GOOD, "operator_id": "admin"})
    assert r.is_error and "operator_id: Extra inputs are not permitted" in r.content[0].text


def test_both_doors_send_the_same_refusal(monkeypatch):
    monkeypatch.setenv("FANRESERVE_OPERATOR", "op-1")
    bad = {**GOOD, "limit": 500}
    fc = call_tool(call(**bad), tools_for("op-1"), "op-1")
    assert mcp_call(bad).content[0].text.endswith(fc["error"])


def test_mcp_annotates_it_read_only():
    async def go():
        async with Client(mcp) as c:
            return {t.name: t for t in (await c.list_tools()).tools}["rank_loyal_fans"].annotations
    a = asyncio.run(go())
    assert a.read_only_hint is True and a.destructive_hint is False
