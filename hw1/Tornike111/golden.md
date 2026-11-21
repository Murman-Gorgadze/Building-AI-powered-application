# HW1 golden questions · Operator reason message

Run on 21 November 2026 with `pytest hw1/Tornike111 -v` (16 passed) and the CLI commands below. The tests replace the model with a fake that returns a fixed reply, so no key is needed.

Decision used in g1 and g2 (`src/examples/reserve.json`): `ucl-1`, RESERVE, score 78, 5000 seats, reasons `tier 1 event (+35)`, `Friday is a busy day (+18)`, `selling fast, 85% sold 21d out (+25)`.

| # | Question (input) | Expected | Actual | Pass? | How I ran it |
|---|---|---|---|---|---|
| 1 | RESERVE decision above; model replies `Hold 5,000 seats: tier 1 Friday match, 85% sold 21 days out.` | that sentence, `source: model`; prompt lists all 3 reasons | the model sentence, `source: model`; all 3 reasons found in the prompt | pass | `tests/test_explain.py::test_g1_grounded_sentence_is_used` |
| 2 | Same decision; model replies `Hold 5,000 seats; fans will pay 40 GEL each and it sells out in 2 hours.` (invented price and time) | template, `source: fallback`, no "40" in the text | `Reserve 5000 seats for ucl-1 (score 78): tier 1 event (+35); Friday is a busy day (+18); selling fast, 85% sold 21d out (+25).`, `source: fallback` | pass | `tests/test_explain.py::test_g2_invented_number_falls_back` |
| 3 | `src/examples/skip.json` (SKIP, score 15); same with WATCH | `null`, zero model calls | `null`; the fake model's call list is `[]` for SKIP and WATCH | pass | `test_g3_non_reserve_makes_no_call`; CLI `python hw1/Tornike111/src/explain.py hw1/Tornike111/src/examples/skip.json --offline` printed `null` |

**Error cases from the CLI.** With no key, `python hw1/Tornike111/src/explain.py hw1/Tornike111/src/examples/reserve.json` printed `model call failed, using fallback: OPENROUTER_API_KEY is not set`, then the template; exit 0. With `src/examples/bad.json` (empty reasons) it printed `error: reasons must be a non-empty list of strings`; exit 2.

All three questions use the fake model; no live model run.

**What I learned from running them.** The number check is what makes g2 pass, and it is also its limit: `Hold the seats, this match always sells out.` has no numbers, so `is_grounded()` returns `True` even though "always sells out" is not a listed reason. Catching that needs a per-claim check or a judge model; it is written down as a risk in `spec.md`.
