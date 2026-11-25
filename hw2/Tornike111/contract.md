# HW2 · Tool contract · `rank_loyal_fans` · Tornike111

**Tool:** `rank_loyal_fans` · **Owner:** `Tornike111` · **Team repo:** https://github.com/Murman-Gorgadze/Building-AI-powered-application
**Code on `main`:** contract class `RankLoyalFans` in [`src/contracts.py`](../../src/contracts.py) line 63 (types `AsOf` line 35, `Limit` line 37) · function `rank_loyal_fans` in [`src/tools.py`](../../src/tools.py) line 99 (loader `load_attendance` line 88) · registry entry in `src/tools.py` line 132 (`TOOLS`) · MCP registration in [`src/mcp_server.py`](../../src/mcp_server.py) line 72 · rule constants `LOYAL_WINDOW_DAYS`, `LOYAL_MIN_VISITS` in [`src/reserve.py`](../../src/reserve.py) lines 28–29
**Product pull request:** [#13](https://github.com/Murman-Gorgadze/Building-AI-powered-application/pull/13) (closes #11) · merged commit `386b533` · full contract section in [`docs/tool-contracts.md`](../../docs/tool-contracts.md), decision [`docs/decisions/0005`](../../docs/decisions/0005-rank-loyal-fans-is-operator-only.md)

**In one sentence, for the model:** Operators only. Which fans count as loyal for one category of event: at least 3 visits in the 90 days up to as_of, most visits first. Returns pseudonymous fan ids (fan-0001), never names. Reads only: it reserves nothing and contacts no one. Use it when the operator asks who would get reserved seats; the loyalty rule is fixed in code and cannot be changed by arguments.

| | |
|---|---|
| **Effect** | reads `data/attendance.json` and ranks it with `rank_fans()`; writes only its own line in `logs/tools.jsonl` |
| **Undo** | nothing to undo: no seat is reserved, no fan is contacted, no record changes |
| **Idempotent?** | yes. Two identical calls (`football`, `2026-11-20`, `op-1`) on 25 Nov returned the same JSON both times: `{"category":"football","as_of":"2026-11-20","window_days":90,"min_visits":3,"total_loyal":5,"fans":[{"fan_id":"fan-0001","visits":6},{"fan_id":"fan-0002","visits":5},{"fan_id":"fan-0003","visits":5},{"fan_id":"fan-0004","visits":4},{"fan_id":"fan-0005","visits":3}]}` |
| **Offered to** | signed-in operators only. `operator_only=True` on its `TOOLS` entry (`src/tools.py` line 132); `tools_for(caller)` drops it when `caller` is `None` |
| **Identity from** | the app, never the model: `needs_caller=True`, so `call_tool()` in `src/act.py` passes the signed-in caller in; the MCP door calls `signed_in_operator()` (`FANRESERVE_OPERATOR`, set by whoever starts the server). The tool refuses a missing caller itself as a backstop |
| **Touches** | `data/attendance.json`, read only (20 made-up fans, `fan-0001` to `fan-0020`). No database, no network, no other file |
| **Must never** | show fan data to an anonymous caller, or let the model change who counts as loyal |

**Inputs.** `extra="forbid"` on the class; no caller, operator or fan field.

| Argument | Type | Constraint (as written in code) | Description the model reads |
|---|---|---|---|
| `category` | string | `Literal["football", "basketball", "rugby", "concert", "theatre", "other"]`; required | Kind of event |
| `as_of` | date | `ge=date(2026, 1, 1), le=date(2026, 12, 31)`; required | Count visits in the 90 days up to and including this date, YYYY-MM-DD, in 2026 |
| `limit` | integer | `ge=1, le=50`; default 10 | Most fans to return, 1 to 50 |

**Expected failures.** The exact strings from `src/tools.py`, `src/act.py` and `src/mcp_server.py`.

| When | Message the model reads |
|---|---|
| an argument breaks the contract or is not in it | `invalid arguments: limit: Input should be less than or equal to 50. Fix or remove only those arguments and call rank_loyal_fans again, using the operator's own numbers; if the operator did not give a value, ask for it.` |
| anonymous caller, function calling | `no tool named 'rank_loyal_fans' is available to you. Tools you can call: check_reserve.` |
| nobody signed in, MCP | `Not signed in: this server was started without FANRESERVE_OPERATOR.` |
| nobody qualifies | `no loyal theatre fans: nobody has 3 or more theatre visits in the 90 days up to 2026-11-20. Tell the operator there is no loyal-fan list for this category; do not lower the bar or invent fan ids.` |
| data file missing or broken | `Attendance data is not available right now, so loyal fans cannot be ranked. Tell the operator; do not guess fan ids.` |

**The decision I had to make.** `rank_fans()` in `src/reserve.py` already took `window_days` and `min_visits` as parameters, so the obvious wrapper would have put them in the contract, and a model could have called the tool with `min_visits: 1` and turned every one-time buyer into a "loyal fan" who gets reserved seats. I took them out: the rule is now the constants `LOYAL_WINDOW_DAYS = 90` and `LOYAL_MIN_VISITS = 3`, and `extra="forbid"` refuses both names if the model sends them (`tests/test_rank_loyal_fans.py::test_contract_refuses_identity_and_rule_changes`). I also chose `as_of` as an argument rather than the clock, so the result is reproducible. Both choices are in `docs/decisions/0005` and in the `src/reserve.py` diff of #13.
