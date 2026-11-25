# HW2 · Tool contract · `check_reserve`

**Tool:** `check_reserve` · **Owner:** `Murman-Gorgadze` · **Team repo:** https://github.com/Murman-Gorgadze/Building-AI-powered-application
**Code on `main`:** contract class `CheckReserve` in [`src/contracts.py` line 43](../../src/contracts.py#L43) · function in [`src/tools.py` line 56](../../src/tools.py#L56) · registry entry in [`src/tools.py` line 85](../../src/tools.py#L85) (`TOOLS`) · MCP registration in [`src/mcp_server.py` line 62](../../src/mcp_server.py#L62)
**Product pull request:** [#9](https://github.com/Murman-Gorgadze/Building-AI-powered-application/pull/9) · merged commit `e7318ae` (merged by Tornike111, 25 Nov 2026)
**Full team contract:** [`docs/tool-contracts.md`](../../docs/tool-contracts.md)

**In one sentence, for the model** (the docstring of `CheckReserve`, copied): Should this event hold back seats for loyal fans, and how many? Runs FanReserve's scoring rules (no model) and returns RESERVE, WATCH or SKIP, the seats to hold and the reasons. Reads only: it places no hold and changes nothing. Pass the numbers the operator gave you; never guess them.

| | |
|---|---|
| **Effect** | reads: computes a decision from its arguments with `decide()` in `src/reserve.py`. It writes nothing except its log line. In Lab 7 terms it is a **read** tool, not a consequential one: calling it in a loop changes nothing, so it needs no yes from a person. The consequential action, placing a hold, is deliberately not a tool |
| **Undo** | nothing to undo: no hold is placed, no event or fan record changes |
| **Idempotent?** | yes. Second identical call through MCP on 25 Nov returned the same result: `{"event_id": "unnamed", "action": "RESERVE", "score": 78, "reserve_seats": 5000, "reasons": ["tier 1 event (+35)", "Friday is a busy day (+18)", "selling fast, 85% sold 21d out (+25)"]}` |
| **Offered to** | everyone, anonymous callers included: `Tool("check_reserve", CheckReserve, check_reserve)` in `TOOLS` leaves `operator_only=False`, and `tools_for()` offers every tool that is not operator-only |
| **Identity from** | not needed. The contract has no caller field; `extra="forbid"` refuses `operator_id` if the model adds one (golden case a3). The function-calling door logs a hash of the caller from `act(question, caller=...)`; the MCP door reads `FANRESERVE_OPERATOR` set by whoever launches the server |
| **Touches** | nothing outside the process: the weights and `HOLIDAYS_2026` at the top of `src/reserve.py`. No file, no database, no network |
| **Must never** | place a hold, or let the model set the outcome: `action`, `score` and `reserve_seats` come only from `decide()` (`docs/decisions/0002`) |

**Inputs** (from `src/contracts.py`; `extra="forbid"` on the base class `Contract`)

| Argument | Type | Constraint (as written in code) | Description the model reads |
|---|---|---|---|
| `category` | string | `Literal["football", "basketball", "rugby", "concert", "theatre", "other"]`, default `"football"` | Kind of event |
| `tier` | int | `ge=1, le=3` | Event tier: 1 = top (Champions League, big tour stop), 3 = minor |
| `day` | date | `ge=date(2026, 1, 1), le=date(2026, 12, 31)` | Event date, YYYY-MM-DD, in 2026 (the holiday list covers 2026 only) |
| `capacity` | int | `ge=1, le=150_000` | Seats in the venue, 1 to 150000 |
| `sold_pct` | float | `ge=0, le=100, allow_inf_nan=False` | Percent of seats already sold, 0 to 100 (not 0 to 1) |
| `days_out` | int | `ge=0, le=365` | Days from today until the event, 0 to 365 |
| `is_tour` | bool | default `False` | True if the event is a stop on a touring artist's or team's tour |
| `event_id` | string | `pattern=r"^[a-z0-9][a-z0-9-]{0,31}$"`, default `"unnamed"` | Short event label for the log, lowercase letters, digits and dashes |

**Expected failures** (exact strings from `src/tools.py`; `<...>` is filled in by the code)

| When | Message the model reads |
|---|---|
| an argument breaks the contract | `invalid arguments: <field>: <what is wrong>. Fix or remove only those arguments and call check_reserve again, using the operator's own numbers; if the operator did not give a value, ask for it.` |
| an argument the contract does not have | the same message with `<field>: Extra inputs are not permitted` |
| a tool that is not offered | `no tool named '<name>' is available to you. Tools you can call: check_reserve.` |
| `decide()` refuses the event (backstop) | `FanReserve refused this event: <reason>. Fix that value and call check_reserve again.` |

**The decision I had to make.** The first version of the MCP door could be handed a made-up outcome: called with `action: RESERVE` and `reserve_seats: 50000`, it quietly ignored those two fields and ran anyway, instead of saying they were not allowed. In FanReserve only the fixed rules in `decide()` may decide whether seats are held and how many; the model may only explain the decision. A system that silently ignores a fake answer is risky, because the model never learns it did something wrong and nobody sees the attempt. So the final version checks our own contract on both doors and clearly refuses (`invalid arguments: action: Extra inputs are not permitted ...`). The change is visible in `docs/decisions/0004-one-contract-check-for-both-doors.md` and in `tests/test_mcp.py::test_an_argument_outside_the_contract_is_refused_not_dropped`.
