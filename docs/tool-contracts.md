# Tool contracts · FanReserve

*One section per tool, from `Lab-5/templates/tool-contract.md`. Every rule here exists in code: the contract class in `src/contracts.py`, the tool body and registry in `src/tools.py`, or the MCP server in `src/mcp_server.py`. If this page and the code disagree, the code is right and this page is a bug.*

Both doors check the same contract and send the same refusal text:
- **Function calling** (`src/act.py`, `call_tool()`): offered? → contract → run, with the caller from the app.
- **MCP** (`src/mcp_server.py`, `FanReserveServer.call_tool()`): contract → run. Our own check runs first because the MCP SDK on its own drops unknown arguments silently instead of refusing them.

`tests/test_mcp.py` fails if the two doors ever describe a tool differently, or refuse differently.

## `check_reserve`

**In one sentence, for the model:** Should this event hold back seats for loyal fans, and how many? Runs FanReserve's scoring rules (no model) and returns RESERVE, WATCH or SKIP, the seats to hold and the reasons. Reads only: it places no hold and changes nothing. Pass the numbers the operator gave you; never guess them.

| | |
|---|---|
| **Effect** | reads: computes a decision from the arguments with `decide()` in `src/reserve.py`; writes nothing but its own log line |
| **Undo** | nothing to undo: no hold is placed, no event or fan record changes |
| **Idempotent?** | yes: the same arguments give the same result (no clock, no randomness, no stored state) |
| **Offered to** | everyone, anonymous callers included: `operator_only=False` on its `TOOLS` entry in `src/tools.py`. It reads no fan data, so offering it widely costs nothing |
| **Identity from** | not needed. The contract has no caller field, and `extra="forbid"` refuses one if the model adds it. The log keeps a 12-character hash of the caller (`caller_key()`), never the id |
| **Touches** | nothing outside the process: the weights and `HOLIDAYS_2026` in `src/reserve.py`. No file, no database, no network |
| **Must never** | place a hold or let the model set the outcome: `action`, `score` and `reserve_seats` come only from `decide()`, never from arguments (`docs/decisions/0002`) |

**Inputs.** `extra="forbid"`; every string has a pattern or a fixed set; every number has bounds.

| Argument | Type | Constraint | Description the model reads |
|---|---|---|---|
| `category` | string | one of `football`, `basketball`, `rugby`, `concert`, `theatre`, `other`; default `football` | Kind of event |
| `tier` | integer | 1 to 3 | Event tier: 1 = top (Champions League, big tour stop), 3 = minor |
| `day` | date | `YYYY-MM-DD`, 2026-01-01 to 2026-12-31 | Event date, YYYY-MM-DD, in 2026 (the holiday list covers 2026 only) |
| `capacity` | integer | 1 to 150000 | Seats in the venue, 1 to 150000 |
| `sold_pct` | number | 0 to 100, no NaN or infinity | Percent of seats already sold, 0 to 100 (not 0 to 1) |
| `days_out` | integer | 0 to 365 | Days from today until the event, 0 to 365 |
| `is_tour` | boolean | default `false` | True if the event is a stop on a touring artist's or team's tour |
| `event_id` | string | pattern `^[a-z0-9][a-z0-9-]{0,31}$`; default `unnamed` | Short event label for the log, lowercase letters, digits and dashes |

**Result** (`ReserveResult`): `event_id` (string), `action` (`RESERVE` · `WATCH` · `SKIP`), `score` (0 to 100), `reserve_seats` (integer, 0 unless `RESERVE`), `reasons` (list of strings, each with its points).

**Expected failures.** The model reads these exact strings (the `<...>` parts are filled in by the code).

| When | Message the model reads (what happened, what to do next) |
|---|---|
| an argument breaks the contract | `invalid arguments: <field>: <what is wrong>. Fix or remove only those arguments and call check_reserve again, using the operator's own numbers; if the operator did not give a value, ask for it.` |
| an argument the contract does not have | the same message, with `<field>: Extra inputs are not permitted` |
| a tool name that is not offered | `no tool named '<name>' is available to you. Tools you can call: check_reserve.` |
| `decide()` refuses the event (backstop; the contract catches these first) | `FanReserve refused this event: <reason>. Fix that value and call check_reserve again.` |

**Tests and golden cases**

| Case | Expect | Where |
|---|---|---|
| a valid call | runs, `RESERVE`, score 78, 5000 seats | `evals/tools/Murman-Gorgadze.yaml` n1 · `tests/test_act.py` · `tests/test_mcp.py` |
| invalid arguments (`sold_pct: 150`) | refused before the tool runs | yaml b1 · `tests/test_act.py::test_invalid_arguments_never_reach_the_tool` |
| not offered to this caller | refused, nothing runs | `tests/test_act.py::test_a_tool_that_does_not_exist_is_not_run` |
| identity in the arguments (`operator_id`) | refused | yaml a3 · `tests/test_act.py::test_model_cannot_choose_the_caller` |
| adversarial: the model dictates `action` and `reserve_seats` | refused, through both doors | yaml a1 · `tests/test_mcp.py::test_an_argument_outside_the_contract_is_refused_not_dropped` |
| adversarial: a path in `event_id` | refused by the pattern | yaml a2 |

**Log line.** Every function-calling call adds one line to `logs/tools.jsonl`: `ts`, `tool`, `arguments` (as the model sent them), `ok`, `error`, `caller` (12-character hash, or `null` for anonymous), `latency_ms`. It leaves out the caller's id and the result. Known gap: calls through the MCP door are not logged yet.

**Known limit.** `day` must be in 2026, because `HOLIDAYS_2026` is the only holiday list. Events in 2027 are refused until the list is extended.

---

## `rank_loyal_fans`

**In one sentence, for the model:** Operators only. Which fans count as loyal for one category of event: at least 3 visits in the 90 days up to as_of, most visits first. Returns pseudonymous fan ids (fan-0001), never names. Reads only: it reserves nothing and contacts no one. Use it when the operator asks who would get reserved seats; the loyalty rule is fixed in code and cannot be changed by arguments.

| | |
|---|---|
| **Effect** | reads: loads `data/attendance.json` and ranks it with `rank_fans()` in `src/reserve.py`; writes nothing but its own log line |
| **Undo** | nothing to undo: no seat is reserved, no fan is contacted, no record changes |
| **Idempotent?** | yes: the same arguments on the same data give the same result (`as_of` is an argument, not the clock) |
| **Offered to** | signed-in operators only: `operator_only=True` on its `TOOLS` entry in `src/tools.py`, so `tools_for(None)` never lists it. It returns fan data, so an anonymous caller must not even see it (`docs/decisions/0005`) |
| **Identity from** | the app, never the model: `needs_caller=True`, so `call_tool()` passes the caller in; the MCP door takes it from `signed_in_operator()` (`FANRESERVE_OPERATOR`, set by whoever starts the server). The contract has no caller or fan field and `extra="forbid"` refuses one. The tool refuses a missing caller itself as a backstop |
| **Touches** | `data/attendance.json` (read only), the constants `LOYAL_WINDOW_DAYS` and `LOYAL_MIN_VISITS` in `src/reserve.py`. No database, no network |
| **Must never** | show fan data to an anonymous caller; let the model change who counts as loyal (no `min_visits` or `window_days` argument); return names or any field beyond the pseudonymous id and a visit count |

**Inputs.** `extra="forbid"`; every string has a fixed set; every number and date has bounds.

| Argument | Type | Constraint | Description the model reads |
|---|---|---|---|
| `category` | string | one of `football`, `basketball`, `rugby`, `concert`, `theatre`, `other`; required | Kind of event |
| `as_of` | date | `YYYY-MM-DD`, 2026-01-01 to 2026-12-31; required | Count visits in the 90 days up to and including this date, YYYY-MM-DD, in 2026 |
| `limit` | integer | 1 to 50; default 10 | Most fans to return, 1 to 50 |

**Result** (`LoyalFansResult`): `category`, `as_of`, `window_days` (90) and `min_visits` (3), echoed so the operator sees the rule; `total_loyal` (how many qualify before `limit`); `fans` (list of `{fan_id, visits}`, most visits first, ties by id).

**Expected failures.** The model reads these exact strings.

| When | Message the model reads (what happened, what to do next) |
|---|---|
| an argument breaks the contract, or one it does not have (`operator_id`, `min_visits`) | `invalid arguments: <field>: <what is wrong>. Fix or remove only those arguments and call rank_loyal_fans again, using the operator's own numbers; if the operator did not give a value, ask for it.` |
| an anonymous caller (function calling) | `no tool named 'rank_loyal_fans' is available to you. Tools you can call: check_reserve.` |
| nobody signed in (MCP) | `Not signed in: this server was started without FANRESERVE_OPERATOR.` |
| nobody qualifies | `no loyal <category> fans: nobody has 3 or more <category> visits in the 90 days up to <as_of>. Tell the operator there is no loyal-fan list for this category; do not lower the bar or invent fan ids.` |
| the data file is missing or broken | `Attendance data is not available right now, so loyal fans cannot be ranked. Tell the operator; do not guess fan ids.` (no path or file name) |

**Tests and golden cases**

| Case | Expect | Where |
|---|---|---|
| football, as of 2026-11-20 | 5 loyal fans, `fan-0001` (6) first, `fan-0002`/`fan-0003` tie broken by id | `evals/tools/Tornike111.yaml` n1 · `tests/test_rank_loyal_fans.py` |
| concert, `limit: 2`, another operator | 2 fans returned, `total_loyal: 3`; a visit on the window's first day counts | yaml n2 |
| theatre | refused: no loyal fans, do not lower the bar | yaml n3 |
| `limit: 500` | refused before the data is read | yaml b1 |
| adversarial: an anonymous caller asks for fan data | not offered, never runs | yaml a1 · `test_anonymous_caller_never_reaches_the_data` |
| adversarial: `operator_id`, `fan_id`, `min_visits: 1` or `window_days: 3650` in the arguments | refused, through both doors | `test_contract_refuses_identity_and_rule_changes` · `test_mcp_refuses_an_operator_id_in_the_arguments` |

**Log line.** The same `logs/tools.jsonl` line as `check_reserve`: the caller as a 12-character hash, and no result, so no fan id is written to the log. Known gap, shared with `check_reserve`: calls through the MCP door are not logged yet.

**Known limits.** The MCP door lists the tool to every client and refuses it at call time when nobody is signed in; the function-calling door hides it completely. `as_of` must be in 2026, the year the attendance data covers. Any signed-in operator may rank any category; per-operator permissions are not modelled yet.

---

## `check_day` (team tool, Lab 5)

**In one sentence, for the model:** Is this date a busy day for events? Looks up the weekday and FanReserve's 2026 list of Georgian public holidays, and returns how many demand points the date alone adds to an event's score, with the reasons. Reads only and changes nothing. Use it when the operator asks about a date, not an event; for a full decision call check_reserve.

| | |
|---|---|
| **Effect** | reads: `day_points()` in `src/reserve.py`, the same function `demand_score()` uses, so the tool and the decision can never disagree about a date |
| **Undo** | nothing to undo |
| **Idempotent?** | yes: same date, same answer (`tests/test_check_day.py::test_same_call_twice_gives_the_same_answer`) |
| **Offered to** | everyone, anonymous callers included: `Tool("check_day", CheckDay, check_day)` leaves `operator_only=False`. It reads no fan data |
| **Identity from** | not needed; the contract has no caller field and refuses one |
| **Touches** | `WEEKDAY_POINTS`, `HOLIDAY_POINTS` and `HOLIDAYS_2026` in `src/reserve.py`. No file, no database, no network |
| **Must never** | accept a holiday list or points from the model: holidays and weights come from code only |

**Inputs.** `extra="forbid"`.

| Argument | Type | Constraint | Description the model reads |
|---|---|---|---|
| `day` | date | `YYYY-MM-DD`, 2026-01-01 to 2026-12-31 | Event date, YYYY-MM-DD, in 2026 (the holiday list covers 2026 only) |

**Result** (`DayResult`): `day`, `weekday` (e.g. `Friday`), `is_holiday`, `is_holiday_eve` (the rules count the day before a holiday too), `day_points` (integer), `reasons` (list of strings with their points; empty when the date adds nothing).

**Expected failures.** Only contract refusals: `invalid arguments: day: <what is wrong>. Fix or remove only those arguments and call check_day again, ...` and the same message for an argument the contract does not have.

**Tests and golden cases**

| Case | Expect | Where |
|---|---|---|
| a valid call | Friday, 18 points | `evals/tools/team.yaml` n1 · `tests/test_check_day.py` |
| invalid arguments (a 2027 date) | refused before the tool runs | yaml b1 · `test_invalid_dates_never_reach_the_tool` |
| identity in the arguments | refused | `test_model_cannot_add_its_own_holidays_or_an_identity` |
| adversarial: the model sends its own `holidays` list | refused, through both doors | yaml a1 · `tests/test_mcp.py::test_check_day_through_the_mcp_door` |
| agrees with the scoring rules | same points as `demand_score()` for the date | `test_agrees_with_the_scoring_rules` |

**Log line.** Same as `check_reserve`: one line per function-calling call in `logs/tools.jsonl`, with a hashed caller.

**Known limit.** The holiday list is 2026 only, and it was written from the agent's knowledge: still to be checked against matsne.gov.ge (see the comment above `HOLIDAYS_2026`).

---

## HW2 owners

No two members wrap the same function, and neither wraps the team's Lab 5 tool (`check_day`) (Lab 5 studio).

| Member | Function wrapped | Tool | Status |
|---|---|---|---|
| Murman-Gorgadze | `decide()` in `src/reserve.py` | `check_reserve` | merged, PR #9 |
| Tornike111 | `rank_fans()` in `src/reserve.py` | `rank_loyal_fans` (operator-only) | confirmed; in Tornike's product pull request |
