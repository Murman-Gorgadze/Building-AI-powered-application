# HW2 · Evidence · `check_reserve`

**Where the cases live:** [`evals/tools/Murman-Gorgadze.yaml`](../../evals/tools/Murman-Gorgadze.yaml), run by `tests/test_tool_golden.py` in CI job `test` (`.github/workflows/ci.yml`, step "Product tests"). No model, no key. Seven cases: 3 normal, 1 bad input, 3 adversarial.

| # | Type | Call, exactly as in the yaml | Expected | Actual result (from `call_tool()`, 25 Nov) | Pass? |
|---|---|---|---|---|---|
| n1 | normal | `{tier: 1, day: "2026-10-23", capacity: 50000, sold_pct: 85, days_out: 21}`, caller `op-1` | RESERVE, score 78, 5000 seats | `{"action": "RESERVE", "score": 78, "reserve_seats": 5000}` | pass |
| n2 | normal | `{category: concert, tier: 2, day: "2026-12-12", capacity: 8000, sold_pct: 10, days_out: 30}`, anonymous | WATCH, score 43, 0 seats | `{"action": "WATCH", "score": 43, "reserve_seats": 0}` | pass |
| n3 | normal | `{tier: 3, day: "2026-11-30", capacity: 3000, sold_pct: 5, days_out: 60}`, caller `op-1` | SKIP, 0 seats | `{"action": "SKIP", "score": 1, "reserve_seats": 0}` | pass |
| b1 | bad-input | n1 with `sold_pct: 150` | refused; error names `sold_pct` | `invalid arguments: sold_pct: Input should be less than or equal to 100. Fix or remove only those arguments and call check_reserve again, using the operator's own numbers; if the operator did not give a value, ask for it.` | pass |
| a1 | adversarial | `{tier: 3, day: "2026-11-30", capacity: 50000, sold_pct: 5, days_out: 60, action: RESERVE, reserve_seats: 50000}` | refused; error names `action` | `invalid arguments: action: Extra inputs are not permitted; reserve_seats: Extra inputs are not permitted. Fix or remove only those arguments and call check_reserve again, ...` | pass |
| a2 | adversarial | n1 with `event_id: "../../logs/usage.jsonl"` | refused by the pattern | `invalid arguments: event_id: String should match pattern '^[a-z0-9][a-z0-9-]{0,31}$'. Fix or remove only those arguments ...` | pass |
| a3 | adversarial | n1 with `operator_id: admin`, anonymous | refused; error names `operator_id` | `invalid arguments: operator_id: Extra inputs are not permitted. Fix or remove only those arguments ...` | pass |

`pytest tests/test_tool_golden.py` on 25 Nov: `8 passed` (7 cases plus the check that every file has 5+ cases with a bad-input and an adversarial one).

**The adversarial case, in one sentence:** a model, or an instruction hidden in an event description it read, tries to make a minor, unsold tier 3 match (5% sold) hold all 50,000 seats by passing `action: RESERVE` and `reserve_seats: 50000` as if they were inputs, when FanReserve's decisions must come only from `decide()`.

**Error messages written for a model (Lab 7).** Before 25 Nov the refusal said only what was wrong (`invalid arguments: sold_pct: Input should be less than or equal to 100`). It now also says what to do next: fix or remove those arguments, use the operator's numbers, ask if a value is missing. The unknown-tool message now lists the tools the caller can use.

**The red run.** Branch `red-hw2-Murman-Gorgadze` · weakened, in `src/contracts.py`:
```diff
-    model_config = ConfigDict(extra="forbid")
+    model_config = ConfigDict()   # RED RUN: extra="forbid" removed on purpose; this PR must not merge
```
pull request [#10](https://github.com/Murman-Gorgadze/Building-AI-powered-application/pull/10) (closed, not merged; branch deleted) · run link https://github.com/Murman-Gorgadze/Building-AI-powered-application/actions/runs/45569121985 · tests that failed, pasted from the CI log (9 failed):
```
FAILED tests/test_act.py::test_model_cannot_choose_the_caller - assert (not True)
FAILED tests/test_mcp.py::test_an_argument_outside_the_contract_is_refused_not_dropped[extra0] - AssertionError: assert (False)
FAILED tests/test_mcp.py::test_an_argument_outside_the_contract_is_refused_not_dropped[extra1] - AssertionError: assert (False)
FAILED tests/test_mcp.py::test_an_argument_outside_the_contract_is_refused_not_dropped[extra2] - AssertionError: assert (False)
FAILED tests/test_mcp.py::test_both_doors_send_the_same_refusal - assert False
FAILED tests/test_tool_golden.py::test_tool_golden_case[Murman-Gorgadze:a1] - AssertionError: Murman-Gorgadze:a1 should be refused but ran: {'event_id': 'unnamed', 'action': 'SKIP', 'score': 1, 'reserve_seats': 0, 'reasons': ['steady sales, 5% sold 60d out (+1)']}
FAILED tests/test_tool_golden.py::test_tool_golden_case[Murman-Gorgadze:a3] - AssertionError: Murman-Gorgadze:a3 should be refused but ran: {'event_id': 'unnamed', 'action': 'RESERVE', 'score': 78, 'reserve_seats': 5000, 'reasons': ['tier 1 event (+35)', 'Friday is a busy day (+18)', 'selling fast, 85% sold 21d out (+25)']}
FAILED tests/test_tools.py::test_contract_refuses_fields_it_did_not_ask_for - Failed: DID NOT RAISE ValidationError
FAILED tests/test_tools.py::test_schema_the_model_sees_comes_from_the_contract - KeyError: 'additionalProperties'
```
merge box on GitHub: **"Required checks failing · Fix the failing required checks."**, the **Merge pull request** button greyed out, "Checks: 2 required failing", "Approvals: 1 still required". Screenshot: [`red-run-merge-blocked.png`](red-run-merge-blocked.png). Rule on `main`: required check `test` and 1 approval, enforced for admins too.

**What the red run taught me.** I did not know GitHub could stop broken code by itself: with the rule on `main`, the merge button simply stayed grey until the checks pass and a teammate approves. The second thing I learned was from case a1. Without `extra="forbid"` nothing crashed and nothing warned: the fake `action: RESERVE` and `reserve_seats: 50000` were thrown away and `decide()` returned SKIP with 0 seats. The result looked safe, but only by luck, and the model was never told its request was not allowed. Only the tests noticed, so a "good-looking" result is not proof the tool is safe.

**The green run.** Product pull request [#9](https://github.com/Murman-Gorgadze/Building-AI-powered-application/pull/9) · run link https://github.com/Murman-Gorgadze/Building-AI-powered-application/actions/runs/45565107868 (Python 3.11.18) · last line of the pytest output for `tests/`: `.........                                                                [100%]`. CI runs `pytest -q` and `pytest.ini` adds `-q`, so no count line is printed: 81 dots, 81 passed. Locally, `pytest tests hw1` on the same commit: `109 passed, 1 xfailed`. After the merge, CI on `main` (commit `e7318ae`) was green too: https://github.com/Murman-Gorgadze/Building-AI-powered-application/actions/runs/45568648896.

**Through the MCP door.** Client: the official MCP Python client (`mcp` 2.3, `Client(StdioServerParameters(...))`), launching `python -m src.mcp_server` over stdio with `FANRESERVE_OPERATOR=op-1`, the same way Claude Code launches it. A script, not a model, so no sentence was typed. The calls, in order, and what came back (25 Nov):

```
list_tools -> ['check_reserve'] | read_only_hint: True

call_tool check_reserve {"tier": 1, "day": "2026-10-23", "capacity": 50000, "sold_pct": 85, "days_out": 21}  [valid]
  is_error=False
  {"event_id": "unnamed", "action": "RESERVE", "score": 78, "reserve_seats": 5000, "reasons": ["tier 1 event (+35)", "Friday is a busy day (+18)", "selling fast, 85% sold 21d out (+25)"]}

call_tool check_reserve {same arguments}  [same call again]
  is_error=False
  {"event_id": "unnamed", "action": "RESERVE", "score": 78, "reserve_seats": 5000, "reasons": [...same...]}

call_tool check_reserve {... "sold_pct": 150 ...}  [bad input]
  is_error=True
  invalid arguments: sold_pct: Input should be less than or equal to 100. Fix or remove only those arguments and call check_reserve again, using the operator's own numbers; if the operator did not give a value, ask for it.

call_tool check_reserve {... "action": "RESERVE", "reserve_seats": 50000}  [adversarial]
  is_error=True
  invalid arguments: action: Extra inputs are not permitted; reserve_seats: Extra inputs are not permitted. Fix or remove only those arguments and call check_reserve again, using the operator's own numbers; if the operator did not give a value, ask for it.
```

Before the fix in `docs/decisions/0004`, the last call returned `is_error=False` and a RESERVE result: the SDK had dropped `action` and `reserve_seats` without saying so.
