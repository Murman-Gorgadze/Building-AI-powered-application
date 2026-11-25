"""FanReserve's tools: the code that acts, behind the contracts in src/contracts.py.

Every tool takes a validated contract object (never raw model output) and returns a pydantic
result. A failure we expected raises ToolFailure with a message written for the model: what
went wrong and what to do next. Anything else is a bug and is allowed to crash loudly.

Least privilege by what we did not build: no tool places a hold, edits an event or contacts
a fan. Placing a hold will be a separate tool that waits for the operator's yes (Week 7).
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Callable, Literal

from pydantic import BaseModel, ValidationError

from .contracts import CheckReserve, Contract, RankLoyalFans
from .reserve import LOYAL_MIN_VISITS, LOYAL_WINDOW_DAYS, Event, decide, rank_fans

ATTENDANCE_PATH = Path(__file__).resolve().parents[1] / "data" / "attendance.json"


class ToolFailure(Exception):
    """An expected failure. The message goes back to the model, so it says what to do next."""


def invalid_arguments(tool: str, e: ValidationError) -> str:
    """The one message both doors send for arguments that break a contract: which field, what was
    wrong, what to do next. No stack trace, no echo of the input, no library name or link.
    Sorted by field, because pydantic's own order differs between versions and between JSON and
    dict input (2.13 put an extra field first on one door and last on the other)."""
    problems = "; ".join(sorted(f"{'.'.join(map(str, x['loc'])) or 'arguments'}: {x['msg']}" for x in e.errors()))
    return (f"invalid arguments: {problems}. Fix or remove only those arguments and call {tool} again, "
            "using the operator's own numbers; if the operator did not give a value, ask for it.")


def unknown_tool(name: str, allowed) -> str:
    offered = ", ".join(sorted(allowed)) or "none"
    return f"no tool named {name!r} is available to you. Tools you can call: {offered}."


def caller_key(caller: str) -> str:
    """Logs keep a short hash of the caller, never the id itself."""
    return hashlib.sha256(caller.encode()).hexdigest()[:12]


# ---------------------------------------------------------------- check_reserve (owner: Murman-Gorgadze)

class ReserveResult(BaseModel):
    event_id: str
    action: Literal["RESERVE", "WATCH", "SKIP"]
    score: int                 # 0..100
    reserve_seats: int         # 0 unless action is RESERVE
    reasons: list[str]         # each with its points, e.g. "Friday is a busy day (+18)"


def check_reserve(args: CheckReserve) -> ReserveResult:
    event = Event(args.event_id, args.category, args.tier, args.day, args.capacity,
                  args.sold_pct, args.days_out, args.is_tour)
    try:
        d = decide(event)
    except ValueError as err:   # the contract already enforces decide()'s rules; this is a backstop
        raise ToolFailure(f"FanReserve refused this event: {err}. Fix that value and call check_reserve again.") from err
    return ReserveResult(event_id=d.event_id, action=d.action, score=d.score,
                         reserve_seats=d.reserve_seats, reasons=d.reasons)


# ---------------------------------------------------------------- rank_loyal_fans (owner: Tornike111)

class LoyalFan(BaseModel):
    fan_id: str                # pseudonymous, e.g. "fan-0001"; never a name
    visits: int                # visits to this category inside the window


class LoyalFansResult(BaseModel):
    category: str
    as_of: date
    window_days: int           # the fixed rule, echoed so the operator sees what "loyal" meant
    min_visits: int
    total_loyal: int           # how many fans qualify, before `limit` cut the list
    fans: list[LoyalFan]       # most visits first, ties by fan id


def load_attendance() -> dict[str, list[tuple[str, date]]]:
    """data/attendance.json as rank_fans() reads it. Any problem becomes one message for the
    model with no path or file name in it."""
    try:
        raw = json.loads(ATTENDANCE_PATH.read_text(encoding="utf-8"))["fans"]
        return {fan: [(cat, date.fromisoformat(day)) for cat, day in visits] for fan, visits in raw.items()}
    except (OSError, KeyError, TypeError, ValueError) as err:
        raise ToolFailure("Attendance data is not available right now, so loyal fans cannot be ranked. "
                          "Tell the operator; do not guess fan ids.") from err


def rank_loyal_fans(args: RankLoyalFans, caller: str | None = None) -> LoyalFansResult:
    if not caller:   # backstop: tools_for() never offers this tool to an anonymous caller
        raise ToolFailure("rank_loyal_fans is for signed-in operators only. Tell the user to sign in "
                          "as an operator; do not call it again until they have.")
    ranked = rank_fans(load_attendance(), args.category, args.as_of)
    if not ranked:
        raise ToolFailure(f"no loyal {args.category} fans: nobody has {LOYAL_MIN_VISITS} or more {args.category} "
                          f"visits in the {LOYAL_WINDOW_DAYS} days up to {args.as_of}. Tell the operator there is "
                          "no loyal-fan list for this category; do not lower the bar or invent fan ids.")
    return LoyalFansResult(category=args.category, as_of=args.as_of, window_days=LOYAL_WINDOW_DAYS,
                           min_visits=LOYAL_MIN_VISITS, total_loyal=len(ranked),
                           fans=[LoyalFan(fan_id=f, visits=n) for f, n in ranked[:args.limit]])


# ---------------------------------------------------------------- the registry

@dataclass(frozen=True)
class Tool:
    name: str
    args: type[Contract]
    run: Callable[..., BaseModel]
    operator_only: bool = False     # True: exposes fan data or acts; never offered to an anonymous caller
    needs_caller: bool = False      # True: run(args, caller=...) gets the caller from us, never the model

    def schema(self) -> dict:
        """What the model sees: name, description and JSON Schema, all from the contract."""
        return {"type": "function", "function": {
            "name": self.name, "description": " ".join(self.args.__doc__.split()),
            "parameters": self.args.model_json_schema()}}


TOOLS = {t.name: t for t in [
    Tool("check_reserve", CheckReserve, check_reserve),
    Tool("rank_loyal_fans", RankLoyalFans, rank_loyal_fans, operator_only=True, needs_caller=True),
]}


def tools_for(caller: str | None) -> dict[str, Tool]:
    """Least privilege by construction: an anonymous caller is never offered an operator-only tool."""
    return {n: t for n, t in TOOLS.items() if caller or not t.operator_only}
