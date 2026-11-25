"""The function-calling door: offered? valid? then run, with the caller from us. Fake model only."""
import json

from src import llm
from src.act import MAX_ROUNDS, act, call_tool, main
from src.tools import tools_for

GOOD = dict(tier=1, day="2026-10-23", capacity=50000, sold_pct=85, days_out=21)


def call(name, **args):
    return {"id": "c1", "name": name, "arguments": json.dumps(args)}


def test_valid_call_runs_and_returns_the_decision():
    out = call_tool(call("check_reserve", **GOOD), tools_for(None), None)
    assert out["ok"] and out["result"]["action"] == "RESERVE" and out["result"]["reserve_seats"] == 5000


def test_invalid_arguments_never_reach_the_tool(monkeypatch):
    monkeypatch.setattr("src.tools.decide", lambda e: (_ for _ in ()).throw(AssertionError("tool ran")))
    out = call_tool(call("check_reserve", **{**GOOD, "sold_pct": 150}), tools_for(None), None)
    assert not out["ok"] and out["error"].startswith("invalid arguments: sold_pct")


def test_a_tool_that_does_not_exist_is_not_run():
    out = call_tool(call("place_hold", event_id="ev-1", seats=5000), tools_for("op-1"), "op-1")
    assert not out["ok"] and "no tool named 'place_hold'" in out["error"]
    assert "Tools you can call: check_day, check_reserve, rank_loyal_fans." in out["error"]   # says what to do next


def test_model_cannot_choose_the_caller():
    out = call_tool(call("check_reserve", **GOOD, operator_id="admin"), tools_for(None), None)
    assert not out["ok"] and "operator_id" in out["error"]


def test_errors_do_not_leak_a_stack_trace_or_a_path():
    out = call_tool({"id": "c1", "name": "check_reserve", "arguments": "{not json"}, tools_for(None), None)
    assert not out["ok"] and out["error"].startswith("invalid arguments")
    assert "Traceback" not in out["error"] and "/src/" not in out["error"]


def test_every_call_writes_one_log_line_with_a_hashed_caller(tool_log):
    call_tool(call("check_reserve", **GOOD), tools_for("op-1"), "op-1")
    call_tool(call("check_reserve", **{**GOOD, "tier": 9}), tools_for("op-1"), "op-1")
    lines = [json.loads(x) for x in tool_log.read_text().splitlines()]
    assert [x["ok"] for x in lines] == [True, False]
    assert all(x["tool"] == "check_reserve" and x["caller"] not in (None, "op-1") for x in lines)


def test_end_to_end_with_a_fake_model():
    def model(messages, schemas):
        if messages[-1]["role"] == "user":
            # anonymous caller: the read-only tools, never the operator-only rank_loyal_fans
            assert [s["function"]["name"] for s in schemas] == ["check_reserve", "check_day"]
            return {"content": None, "tool_calls": [call("check_reserve", **GOOD)]}
        result = json.loads(messages[-1]["content"])
        return {"content": f"{result['action']}: hold {result['reserve_seats']:,} seats.", "tool_calls": []}

    reply = act("Should the 23 Oct match hold seats?", model=model)
    assert reply.status == "answered" and reply.text == "RESERVE: hold 5,000 seats." and reply.calls[0]["ok"]


def test_the_model_reads_the_error_and_can_repair():
    turns = []

    def model(messages, schemas):
        turns.append(messages[-1])
        if len(turns) == 1:   # first try is out of range; the error must tell the model which field
            return {"content": None, "tool_calls": [call("check_reserve", **{**GOOD, "sold_pct": 150})]}
        if len(turns) == 2:
            assert "less than or equal to 100" in json.loads(messages[-1]["content"])["error"]
            return {"content": None, "tool_calls": [call("check_reserve", **GOOD)]}
        return {"content": "RESERVE.", "tool_calls": []}

    reply = act("Hold seats?", model=model)
    assert reply.text == "RESERVE." and [c["ok"] for c in reply.calls] == [False, True]


def test_loop_stops_after_the_budget():
    def stubborn(messages, schemas):
        return {"content": None, "tool_calls": [call("check_reserve", tier="top")]}

    reply = act("Hold seats?", model=stubborn)
    assert reply.status == "stopped" and len(reply.calls) == MAX_ROUNDS


def test_no_key_stops_cleanly_without_running_a_tool():
    reply = act("Hold seats?")   # conftest removed OPENROUTER_API_KEY
    assert reply.status == "stopped" and "unavailable" in reply.text and reply.calls == []


def test_reasoning_details_are_echoed_back():
    seen = []

    def model(messages, schemas):
        seen.append(list(messages))
        if len(seen) == 1:
            return {"content": None, "reasoning_details": [{"type": "reasoning.encrypted", "data": "x"}],
                    "tool_calls": [call("check_reserve", **GOOD)]}
        return {"content": "ok", "tool_calls": []}

    act("Hold seats?", model=model)
    assistant = [m for m in seen[1] if m["role"] == "assistant"][0]
    assert assistant["reasoning_details"] == [{"type": "reasoning.encrypted", "data": "x"}]


def test_complete_tools_logs_usage_and_returns_the_tool_calls(monkeypatch, usage_log):
    from types import SimpleNamespace as NS
    tc = NS(id="t1", function=NS(name="check_reserve", arguments=json.dumps(GOOD)))
    resp = NS(usage=NS(prompt_tokens=300, completion_tokens=20),
              choices=[NS(message=NS(content=None, tool_calls=[tc], model_extra={}))])
    monkeypatch.setattr(llm, "client", lambda: NS(chat=NS(completions=NS(create=lambda **kw: resp))))
    msg = llm.complete_tools([{"role": "user", "content": "q"}], [])
    assert msg["tool_calls"] == [{"id": "t1", "name": "check_reserve", "arguments": json.dumps(GOOD)}]
    logged = json.loads(usage_log.read_text().splitlines()[-1])
    assert (logged["feature"], logged["tokens_in"], logged["ok"]) == ("act", 300, True)


def test_cli_exit_code_reflects_the_outcome(capsys):
    assert main(["Hold seats?"]) == 1   # no key: stopped, exit 1
    assert "[stopped]" in capsys.readouterr().out
