"""Tool contracts: what each tool accepts, as types the code checks (docs/tool-contracts.md).

One source of truth for tool inputs, read by two doors:
  * src/tools.py builds the function-calling schema the model sees from the classes below
  * src/mcp_server.py builds the MCP tools from the same type aliases
tests/test_mcp.py fails if the two doors ever describe a tool differently.

Rules for every contract:
  * extra="forbid": an argument we did not ask for is refused, never silently dropped
  * every string has a pattern or a fixed set of values; every number has bounds
  * nothing here says WHO is calling. The caller comes from the app (src/act.py) or the
    server (src/mcp_server.py), never from the model.
"""
from __future__ import annotations

from datetime import date
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

# ---------------------------------------------------------------- shared types

Category = Annotated[Literal["football", "basketball", "rugby", "concert", "theatre", "other"],
                     Field(description="Kind of event")]
Tier = Annotated[int, Field(ge=1, le=3, description="Event tier: 1 = top (Champions League, big tour stop), 3 = minor")]
EventDay = Annotated[date, Field(ge=date(2026, 1, 1), le=date(2026, 12, 31),
                                 description="Event date, YYYY-MM-DD, in 2026 (the holiday list covers 2026 only)")]
Capacity = Annotated[int, Field(ge=1, le=150_000, description="Seats in the venue, 1 to 150000")]
SoldPct = Annotated[float, Field(ge=0, le=100, allow_inf_nan=False,
                                 description="Percent of seats already sold, 0 to 100 (not 0 to 1)")]
DaysOut = Annotated[int, Field(ge=0, le=365, description="Days from today until the event, 0 to 365")]
IsTour = Annotated[bool, Field(description="True if the event is a stop on a touring artist's or team's tour")]
EventId = Annotated[str, Field(pattern=r"^[a-z0-9][a-z0-9-]{0,31}$",
                               description="Short event label for the log, lowercase letters, digits and dashes")]


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid")


# ---------------------------------------------------------------- check_reserve (owner: Murman-Gorgadze, HW2)

class CheckReserve(Contract):
    """Should this event hold back seats for loyal fans, and how many? Runs FanReserve's scoring
    rules (no model) and returns RESERVE, WATCH or SKIP, the seats to hold and the reasons.
    Reads only: it places no hold and changes nothing. Pass the numbers the operator gave you;
    never guess them."""
    category: Category = "football"
    tier: Tier
    day: EventDay
    capacity: Capacity
    sold_pct: SoldPct
    days_out: DaysOut
    is_tour: IsTour = False
    event_id: EventId = "unnamed"
