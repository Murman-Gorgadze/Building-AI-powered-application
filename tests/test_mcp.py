"""The MCP door: same contracts, read-only annotations, readable errors. In-memory client, offline."""
import asyncio

import pytest
from mcp import Client

from src import tools
from src.mcp_server import mcp, signed_in_operator

GOOD = {"tier": 1, "day": "2026-10-23", "capacity": 50000, "sold_pct": 85, "days_out": 21}


def run(coro):
    return asyncio.run(coro)


async def listed():
    async with Client(mcp) as c:
        return {t.name: t for t in (await c.list_tools()).tools}


async def call(name, args):
    async with Client(mcp) as c:
        return await c.call_tool(name, args)


def strip(schema):
    return {k: {kk: vv for kk, vv in v.items() if kk != "title"} for k, v in schema["properties"].items()}


def test_same_tools_through_both_doors():
    assert set(run(listed())) == set(tools.TOOLS)


@pytest.mark.parametrize("name", sorted(tools.TOOLS))
def test_both_doors_describe_the_arguments_identically(name):
    mcp_schema = run(listed())[name].input_schema
    fc_schema = tools.TOOLS[name].schema()["function"]["parameters"]
    assert strip(mcp_schema) == strip(fc_schema)
    assert set(mcp_schema.get("required", [])) == set(fc_schema.get("required", []))


def test_check_reserve_is_annotated_read_only():
    a = run(listed())["check_reserve"].annotations
    assert a.read_only_hint is True and a.destructive_hint is False and a.idempotent_hint is True


def test_valid_call_returns_the_decision_as_structured_data():
    r = run(call("check_reserve", GOOD))
    assert not r.is_error
    assert r.structured_content["action"] == "RESERVE" and r.structured_content["reserve_seats"] == 5000


def test_bad_arguments_are_rejected_with_a_message_for_the_model():
    r = run(call("check_reserve", {**GOOD, "sold_pct": 150}))
    text = r.content[0].text
    assert r.is_error and "sold_pct" in text and "call check_reserve again" in text
    assert "pydantic" not in text and "validation error for" not in text and "input_value" not in text


@pytest.mark.parametrize("extra", [{"action": "RESERVE"}, {"reserve_seats": 50000}, {"operator_id": "admin"}])
def test_an_argument_outside_the_contract_is_refused_not_dropped(extra):
    """The SDK alone would drop these and run the tool; the contract (extra="forbid") refuses them."""
    r = run(call("check_reserve", {**GOOD, **extra}))
    assert r.is_error and "extra inputs are not permitted" in r.content[0].text.lower()


def test_both_doors_send_the_same_refusal():
    import json
    from src.act import call_tool
    bad = {**GOOD, "sold_pct": 150, "action": "RESERVE"}
    fc = call_tool({"id": "1", "name": "check_reserve", "arguments": json.dumps(bad)}, tools.tools_for(None), None)
    assert run(call("check_reserve", bad)).content[0].text.endswith(fc["error"])
    assert fc["error"].startswith("invalid arguments: action: Extra inputs are not permitted; sold_pct: ")  # sorted


def test_expected_failure_reaches_the_model_as_text(monkeypatch):
    def boom(e):
        raise ValueError("tier must be 1..3, got 9")
    monkeypatch.setattr("src.tools.decide", boom)
    r = run(call("check_reserve", GOOD))
    assert r.is_error and "call check_reserve again" in r.content[0].text


def test_operator_comes_from_the_server_not_the_model(monkeypatch):
    with pytest.raises(Exception, match="Not signed in"):
        signed_in_operator()
    monkeypatch.setenv("FANRESERVE_OPERATOR", "op-1")
    assert signed_in_operator() == "op-1"
    assert not set(run(listed())["check_reserve"].input_schema["properties"]) & {"operator", "operator_id", "caller"}


def test_check_day_through_the_mcp_door():
    """Lab 5: the team tool answers through the MCP client, read-only, with the same refusals."""
    assert run(listed())["check_day"].annotations.read_only_hint is True
    r = run(call("check_day", {"day": "2026-05-12"}))
    assert not r.is_error and r.structured_content["is_holiday"] is True and r.structured_content["day_points"] == 12
    r = run(call("check_day", {"day": "2026-11-30", "holidays": ["2026-11-30"]}))
    assert r.is_error and "holidays: Extra inputs are not permitted" in r.content[0].text
