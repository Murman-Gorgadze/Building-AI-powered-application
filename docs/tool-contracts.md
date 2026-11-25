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

## HW2 owners

No two members wrap the same function (Lab 5 studio).

| Member | Function wrapped | Tool | Status |
|---|---|---|---|
| Murman-Gorgadze | `decide()` in `src/reserve.py` | `check_reserve` | this pull request |
| Tornike111 | `rank_fans()` in `src/reserve.py` | `rank_loyal_fans` (operator-only) | proposed; Tornike confirms in his review |
