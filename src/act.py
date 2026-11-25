"""Function calling: the model asks for a tool, our code decides whether it runs.

The loop:
  1. send the question plus the schemas of the tools THIS caller may use
  2. no tool call in the reply -> that is the answer
  3. each tool call goes through call_tool(): offered? valid? then run, with the caller from us
  4. results (or errors) go back to the model as tool messages; at most MAX_ROUNDS model turns

call_tool() never raises. Whatever happens becomes a dict the model can read and one line in
logs/tools.jsonl (the log half of the Evidence Rule for actions).

Run:  python -m src.act "Should the 23 Oct tier 1 match (50000 seats, 85% sold, 21 days out) hold seats?"
      python -m src.act --operator op-1 "..."     (the operator id is the stand-in for sign-in)
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from pydantic import ValidationError

from . import llm
from .tools import Tool, ToolFailure, caller_key, invalid_arguments, tools_for, unknown_tool

MAX_ROUNDS = 3   # budget: three model turns, then stop and say so

SYSTEM = """You are FanReserve, an assistant for ticketing operators. You help decide which events
hold seats back for loyal fans. Use a tool for every decision: never compute a score, an action
or a seat count yourself, and never invent a tool result. Use only numbers the operator gave you.
If a tool returns an error, read it: fix your arguments once, or tell the operator what is missing.
Nothing you do places a hold; say so if the operator asks you to place one."""


def tool_log_path() -> Path:
    return Path(os.environ.get("FANRESERVE_TOOL_LOG", "logs/tools.jsonl"))


@dataclass
class Reply:
    status: str                                       # "answered" or "stopped"
    text: str
    calls: list[dict] = field(default_factory=list)   # one entry per tool call, as logged

    def to_dict(self) -> dict:
        return asdict(self)


def call_tool(call: dict, allowed: dict[str, Tool], caller: str | None) -> dict:
    t0 = time.perf_counter()
    tool = allowed.get(call["name"])
    if tool is None:                                                     # gate 1 · offered to this caller?
        return _log(call, caller, t0, error=unknown_tool(call["name"], allowed))
    try:
        args = tool.args.model_validate_json(call["arguments"] or "{}")  # gate 2 · the contract
    except ValidationError as e:
        return _log(call, caller, t0, error=invalid_arguments(tool.name, e))
    try:
        out = tool.run(args, caller=caller) if tool.needs_caller else tool.run(args)   # gate 3 · caller from us
    except ToolFailure as e:
        return _log(call, caller, t0, error=str(e))
    return _log(call, caller, t0, result=out.model_dump(mode="json"))


def act(question: str, caller: str | None = None, model=None) -> Reply:
    model = model or llm.complete_tools
    allowed = tools_for(caller)
    messages = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": question}]
    calls: list[dict] = []
    for _ in range(MAX_ROUNDS):
        try:
            msg = model(messages, [t.schema() for t in allowed.values()])
        except llm.LLMUnavailable as err:
            return Reply("stopped", f"The model is unavailable ({err}). Run python -m src.reserve directly.", calls)
        if not msg["tool_calls"]:
            return Reply("answered", msg["content"] or "", calls)
        messages.append(as_assistant(msg))
        for c in msg["tool_calls"]:
            outcome = call_tool(c, allowed, caller)
            calls.append(outcome)
            messages.append({"role": "tool", "tool_call_id": c["id"],
                             "content": json.dumps(outcome["result"] if outcome["ok"] else {"error": outcome["error"]})})
    return Reply("stopped", f"I could not finish that in {MAX_ROUNDS} steps. Nothing was changed.", calls)


def as_assistant(msg: dict) -> dict:
    """Echo the model's turn back exactly. Gemini 3 rejects the next call unless its
    reasoning_details come back unmodified between tool turns."""
    out = {"role": "assistant", "content": msg["content"],
           "tool_calls": [{"id": c["id"], "type": "function",
                           "function": {"name": c["name"], "arguments": c["arguments"]}}
                          for c in msg["tool_calls"]]}
    if msg.get("reasoning_details"):
        out["reasoning_details"] = msg["reasoning_details"]
    return out


def _log(call: dict, caller: str | None, t0: float, result: dict | None = None,
         error: str | None = None) -> dict:
    line = {"ts": datetime.now(timezone.utc).isoformat(timespec="seconds"), "tool": call["name"],
            "arguments": call["arguments"], "ok": error is None, "error": error,
            "caller": caller_key(caller) if caller else None,
            "latency_ms": round((time.perf_counter() - t0) * 1000, 2)}
    path = tool_log_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(line) + "\n")
    return {**line, "result": result}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Ask FanReserve a question; the model may call tools")
    p.add_argument("question")
    p.add_argument("--operator", default=os.environ.get("FANRESERVE_OPERATOR"),
                   help="signed-in operator id (stand-in for real sign-in); never comes from the model")
    a = p.parse_args(argv)
    reply = act(a.question, caller=a.operator)
    for c in reply.calls:
        print(f"tool {c['tool']} ok={c['ok']}" + (f" error={c['error']}" if c["error"] else ""))
    print(f"[{reply.status}] {reply.text}")
    return 0 if reply.status == "answered" else 1


if __name__ == "__main__":
    sys.exit(main())
