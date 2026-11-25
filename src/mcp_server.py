"""FanReserve as an MCP server: the same tools as src/tools.py, for any MCP host.

Run over stdio (what Claude Code, Cursor and VS Code launch):
    FANRESERVE_OPERATOR=op-1 python -m src.mcp_server
Connect it to Claude Code from the repo root:
    claude mcp add --env FANRESERVE_OPERATOR=op-1 --transport stdio fanreserve -- python -m src.mcp_server

MCP Python SDK 2.x (MCPServer, formerly FastMCP). Each tool's schema comes from the type hints,
which come from src/contracts.py; tests/test_mcp.py checks both doors stay identical.

The SDK checks arguments against the type hints, but it silently drops an argument it does not
know (an `action: RESERVE` the model made up would vanish instead of being refused) and its error
text names pydantic and links to its docs. So every call is checked against our own contract
first, with the same message src/act.py sends: one gate, two doors.
"""
from __future__ import annotations

import os
import sys

from pydantic import ValidationError
from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import ToolAnnotations

from . import tools
from .contracts import Capacity, Category, CheckReserve, DaysOut, EventDay, EventId, IsTour, SoldPct, Tier

class FanReserveServer(MCPServer):
    async def call_tool(self, name, arguments, context=None):
        tool = tools.TOOLS.get(name)
        if tool is None:
            raise ToolError(tools.unknown_tool(name, tools.TOOLS))
        try:
            tool.args.model_validate(arguments)          # the contract, extra="forbid" included
        except ValidationError as e:
            raise ToolError(tools.invalid_arguments(name, e)) from None
        return await super().call_tool(name, arguments, context)


mcp = FanReserveServer("fanreserve", instructions="FanReserve: which events hold seats back for loyal fans, and why.")
READS = ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=False)


def signed_in_operator() -> str:
    """Who is calling. Set by whoever launches the server, never by the model.
    Operator-only tools take it with `caller: Annotated[str, Resolve(signed_in_operator)]`."""
    operator = os.environ.get("FANRESERVE_OPERATOR")
    if not operator:
        raise ToolError("Not signed in: this server was started without FANRESERVE_OPERATOR.")
    return operator


def _run(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except tools.ToolFailure as e:   # expected failures reach the model as readable errors
        raise ToolError(str(e)) from e


@mcp.tool(annotations=READS, description=" ".join(CheckReserve.__doc__.split()))
def check_reserve(tier: Tier, day: EventDay, capacity: Capacity, sold_pct: SoldPct, days_out: DaysOut,
                  category: Category = "football", is_tour: IsTour = False,
                  event_id: EventId = "unnamed") -> tools.ReserveResult:
    return _run(tools.check_reserve, CheckReserve(category=category, tier=tier, day=day, capacity=capacity,
                                                  sold_pct=sold_pct, days_out=days_out, is_tour=is_tour,
                                                  event_id=event_id))


if __name__ == "__main__":
    if "--http" in sys.argv:
        mcp.run("streamable-http", host="127.0.0.1", port=8000)
    else:
        mcp.run()
