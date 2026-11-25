# HW2 · Evidence · `rank_loyal_fans` · Tornike111

**Where the cases live:** [`evals/tools/Tornike111.yaml`](../../evals/tools/Tornike111.yaml), run by `tests/test_tool_golden.py` in CI job `test` (`ci / test`, required on `main`). Data: `data/attendance.json`, made-up fan ids. Window for `as_of: 2026-11-20` is 2026-08-22 to 2026-11-20.

| # | Type | Call, exactly as in the yaml | Expected | Actual result (25 Nov, `call_tool()` on `main`) | Pass? |
|---|---|---|---|---|---|
| n1 | normal | caller `op-1` · `{category: football, as_of: "2026-11-20"}` | ok, `total_loyal: 5`, `fan-0001` (6), `fan-0002` (5), `fan-0003` (5), `fan-0004` (4), `fan-0005` (3) | `"total_loyal": 5, "fans": [{"fan_id": "fan-0001", "visits": 6}, {"fan_id": "fan-0002", "visits": 5}, {"fan_id": "fan-0003", "visits": 5}, {"fan_id": "fan-0004", "visits": 4}, {"fan_id": "fan-0005", "visits": 3}]` | pass |
| n2 | normal | caller `op-2` · `{category: concert, as_of: "2026-11-20", limit: 2}` | ok, 2 fans returned, `total_loyal: 3` | `"total_loyal": 3, "fans": [{"fan_id": "fan-0008", "visits": 5}, {"fan_id": "fan-0007", "visits": 4}]` | pass |
| n3 | normal | caller `op-1` · `{category: theatre, as_of: "2026-11-20"}` | refused: "no loyal theatre fans", "do not lower the bar" | `no loyal theatre fans: nobody has 3 or more theatre visits in the 90 days up to 2026-11-20. Tell the operator there is no loyal-fan list for this category; do not lower the bar or invent fan ids.` | pass |
| b1 | bad-input | caller `op-1` · `{category: football, as_of: "2026-11-20", limit: 500}` | refused before the data is read: "invalid arguments", "limit" | `invalid arguments: limit: Input should be less than or equal to 50. Fix or remove only those arguments and call rank_loyal_fans again, using the operator's own numbers; if the operator did not give a value, ask for it.` | pass |
| a1 | adversarial | caller `null` · `{category: football, as_of: "2026-11-20"}` | refused, the tool is never offered | `no tool named 'rank_loyal_fans' is available to you. Tools you can call: check_reserve.` | pass |

**The adversarial case, in one sentence:** someone who is not signed in, or a model in a public fan chat, asks for the list of FanReserve's most loyal football fans, hoping to see which fan ids get reserved seats so they can target those accounts or copy their pattern.

**The red run.** Branch `red-hw2-Tornike111` · weakened in `src/tools.py`:
```diff
-    Tool("rank_loyal_fans", RankLoyalFans, rank_loyal_fans, operator_only=True, needs_caller=True),
+    Tool("rank_loyal_fans", RankLoyalFans, rank_loyal_fans, operator_only=False, needs_caller=True),
```
Pull request [#14](https://github.com/Murman-Gorgadze/Building-AI-powered-application/pull/14) (closed, not merged; branch deleted) · run: https://github.com/Murman-Gorgadze/Building-AI-powered-application/actions/runs/45573098871/job/139064307288 · failed, pasted from the CI log:
```
FAILED tests/test_act.py::test_end_to_end_with_a_fake_model - AssertionError: assert ['check_reser...k_loyal_fans'] == ['check_reserve']
FAILED tests/test_rank_loyal_fans.py::test_offered_to_operators_only - AssertionError: assert 'rank_loyal_fans' not in {...}
FAILED tests/test_rank_loyal_fans.py::test_anonymous_caller_never_reaches_the_data - assert (not False and "no tool named 'rank_loyal_fans'" in 'rank_loyal_fans is for signed-in operators only. ...')
FAILED tests/test_tool_golden.py::test_tool_golden_case[Tornike111:a1] - AssertionError: error was: rank_loyal_fans is for signed-in operators only. Tell the user to sign in as an operator; do not call it again until they have.
Error: Process completed with exit code 1.
```
Merge box on GitHub: **"All checks have failed · 2 failing checks"** (`ci / test (pull_request)` and `ci / test (push)`, both Required) and **"Merging is blocked"**, with the *Merge pull request* button greyed out.

**What the red run taught me.** I expected `a1` to fail because fan data leaked. It did not leak: the error in the CI log is my own backstop, `rank_loyal_fans is for signed-in operators only`, because the tool checks `caller` itself. So the case failed for a different reason than I expected: the tool was *offered* to an anonymous caller, its name and description were in front of the model, and only the second lock stopped it. With one lock left, the next refactor of the tool body could remove the data protection without any test noticing, so CI blocking here is right. The other surprise was `test_act.py::test_end_to_end_with_a_fake_model`: a test Murman wrote for `check_reserve` also failed, because it checks exactly which tools an anonymous caller sees. A teammate's test protects my tool.

**The green run.** Product pull request [#13](https://github.com/Murman-Gorgadze/Building-AI-powered-application/pull/13) · run: https://github.com/Murman-Gorgadze/Building-AI-powered-application/actions/runs/45571835112/job/139060106456 · step "Product tests (no key, no network)", `pytest -q tests`: the log shows only progress dots (the repo's `pytest.ini` keeps it quiet), 72 dots to `[ 59%]` and 49 more to `[100%]`, no `F` or `E`: **121 passed**, the same count as `pytest tests` on my machine on 25 Nov (`121 passed in 1.43s`)

**Through the MCP door.** Claude Code (VS Code extension), server added through `.mcp.json` as `python -m src.mcp_server` with `FANRESERVE_OPERATOR=op-1`; `/mcp` showed `fanreserve` with 2 tools. I typed: *"Who are the loyal football fans as of 20 November 2026?"* It made one call, `rank_loyal_fans(category="football", as_of="2026-11-20", limit=50)`, and answered with a table of five fans: `fan-0001` (6), `fan-0002` (5), `fan-0003` (5), `fan-0004` (4), `fan-0005` (3). It added that this is everyone who qualifies, that the tool returns ids and never names, and that nothing was reserved or sent. Same five as golden case n1.
