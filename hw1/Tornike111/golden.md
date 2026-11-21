# HW1 golden questions · Operator reason message

Run on 21 November 2026 with `pytest hw1/Tornike111 -v` (18 passed, 1 xfailed) and the CLI commands below. The tests replace the model with a fake that returns a fixed reply, so no key is needed.

Decision used in g1, g2 and g4 (`src/examples/reserve.json`): `ucl-1`, RESERVE, score 78, 5000 seats, reasons `tier 1 event (+35)`, `Friday is a busy day (+18)`, `selling fast, 85% sold 21d out (+25)`.

| # | Question (input) | Expected | Actual | Pass? | How I ran it |
|---|---|---|---|---|---|
| 1 | RESERVE decision above; model replies `Hold 5,000 seats: tier 1 Friday match, 85% sold 21 days out.` | that sentence, `source: model`; prompt lists all 3 reasons | the model sentence, `source: model`; all 3 reasons found in the prompt | pass | `tests/test_explain.py::test_g1_grounded_sentence_is_used` |
| 2 | Same decision; model replies `Hold 5,000 seats; fans will pay 40 GEL each and it sells out in 2 hours.` (invented price and time) | template, `source: fallback`, no "40" in the text | `Reserve 5000 seats for ucl-1 (score 78): tier 1 event (+35); Friday is a busy day (+18); selling fast, 85% sold 21d out (+25).`, `source: fallback` | pass | `tests/test_explain.py::test_g2_invented_number_falls_back` |
| 3 | `src/examples/skip.json` (SKIP, score 15); same with WATCH | `null`, zero model calls | `null`; the fake model's call list is `[]` for SKIP and WATCH | pass | `test_g3_non_reserve_makes_no_call`; CLI `python hw1/Tornike111/src/explain.py hw1/Tornike111/src/examples/skip.json --offline` printed `null` |
| 4 | Same decision; model replies `Hold 5000 seats: 78% sold, score 85.` (85 and 78 swapped: the real figures are 85% sold and score 78) | template, `source: fallback` | the model sentence, `source: model`: every number appears somewhere in the decision, so the check accepts it | **fail (known limit)** | `test_g4_swapped_numbers_known_limit`, marked `xfail`; pytest reports `1 xfailed` |

**Error cases from the CLI.** With no key, `python hw1/Tornike111/src/explain.py hw1/Tornike111/src/examples/reserve.json` printed `model call failed, using fallback: OPENROUTER_API_KEY is not set`, then the template; exit 0. With `src/examples/bad.json` (empty reasons) it printed `error: reasons must be a non-empty list of strings`; exit 2.

All four questions use the fake model.

**Live runs (21 Nov 2026, OpenRouter free models, key from `OPENROUTER_API_KEY`).** No live run returned a model sentence, so the questions above still use the fake model. What the live runs did show:

| Model | What happened | What I did |
|---|---|---|
| `google/gemma-4-31b-it:free`, `google/gemma-4-26b-a4b-it:free`, `liquid/lfm-3-1.7b:free` (2nd try) | `HTTP Error 429: Too Many Requests` → template, `source: fallback`, exit 0 | nothing to fix: this is criterion 4 working on a real failure. Not logged, because no response and no tokens came back |
| `nvidia/nemotron-3.5-super-vl:free` (1st try) | `'NoneType' object has no attribute 'strip'`: the reply had `content = None`, and `llm.py` crashed **before** logging the call | fixed: `llm.py` now logs the call, then raises `model returned no text`; new test `test_llm_empty_reply_is_logged_then_raises` |
| same model (2nd try), `nvidia/nemotron-3.5-lightning:free`, `liquid/lfm-3-1.7b:free` | `model returned no text (finish_reason: length)`: 120 of 120 output tokens used. These models "think" first, and the thinking used the whole cap | raised `max_tokens` from 120 to 1000 (a ceiling, not a charge) |
| `nvidia/nemotron-3.5-lightning:free` (cap 1000) | 1000 of 1000 output tokens, still no text | stopped: free models were busy or thinking too long; documented here |

Evidence: 4 lines in `src/logs/usage.jsonl` (116–129 tokens in, 120 or 1000 out, 1.3–5.6 s, $0). The measured input tokens replaced the estimate in the napkin math in `spec.md`.

A second thing the live runs exposed: with `HW1_MODEL` set to a free model in my terminal, `test_llm_logs_usage` failed (cost 0.0), because the default model comes from the environment. Fixed by naming the model in the test.

**What I learned from running them.** The number check is what makes g2 pass, and it is also its limit: `Hold the seats, this match always sells out.` has no numbers, so `is_grounded()` returns `True` even though "always sells out" is not a listed reason. Catching that needs a per-claim check or a judge model; it is written down as a risk in `spec.md`.
