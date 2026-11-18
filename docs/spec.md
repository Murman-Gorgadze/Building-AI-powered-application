# Spec · FanReserve · MG-TV

*Living spec. v1 started as `hw1/Murman-Gorgadze/spec.md` (HW1) and was copied here on 18 November 2026. Spec keeper: Murman-Gorgadze.*

**Run, from a fresh clone:**
```
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
pytest                                   # product tests: no key, no network
python -m src.reserve --tier 1 --day 2026-10-23 --capacity 50000 --sold 85 --days-out 21
python -m src.reason  --tier 1 --day 2026-10-23 --capacity 50000 --sold 85 --days-out 21   # model reason if OPENROUTER_API_KEY is exported, template otherwise
```

## Goal
Decide which upcoming events should hold seats back for loyal fans, how many, and why, so regular fans are not shut out of sell-outs and organisers do not waste inventory on events that would sell anyway.

## Users
- **Operator** (ticketing manager): reviews decisions each day and approves every hold.
- **Loyal fan:** at least 3 visits to one event category in the last 90 days.

## Success criteria
| # | Criterion | Measured by | Status |
|---|---|---|---|
| S1 | RESERVE decisions are right (event sold out or ≥ 95% full) at least 75% of the time | backtest script over ≥ 50 past events | **planned**: no past-event data yet |
| S2 | Every operator reason restates only `decide()`'s facts, or the template is used | `tests/test_reason.py` | **met in tests** (7 passing) |
| S3 | Median cost per model call under $0.005, p95 latency under 4 s | `logs/usage.jsonl` | **planned**: needs the first live calls |
| S4 | `decide()` answers in under 200 ms with no model call | `tests/test_reserve.py`, decision 0001 | **met** |

## Slices
| Slice | What | Status |
|---|---|---|
| 1 · `decide()` + `rank_fans()` | rule-based score, WATCH band, fan ranking (`src/reserve.py`) | **done**, from HW1 |
| 2 · operator reason | one grounded sentence per RESERVE, through `src/llm.py` (`src/reason.py`) | **done**, waiting for the first live log line |
| 3 · tool contract (HW2) | `decide()` as a typed, read-only tool: tier 1..3, sold_pct 0..100, no write access; MCP server; 5 golden cases incl. one adversarial | planned, Lab 5 / HW2 |
| 4 · fan Q&A with citations | retrieval over reserve rules, calendar and FAQ; refuse when nothing relevant is found | planned |
| 5 · ticket-photo attendance | extract event, date, category with evidence and confidence; low confidence goes to review | planned |
| 6 · operator agent | reviews the week's events, proposes holds, waits for a yes before any hold | planned, Lab 7 |

## Acceptance criteria (slices 1 and 2)
1. Tier 1, Fri 2026-10-23, capacity 50,000, 85% sold, 21 days out → RESERVE, score 78, 5,000 seats (10% for tier 1).
2. Tier 3, Tue 2026-10-27, capacity 8,000, 30% sold, 20 days out → SKIP, score 15, 0 seats; the reason says "steady sales", not "selling fast".
3. `rank_fans()` counts only the requested category, only visits in `[today − 90 days, today]`, keeps fans with ≥ 3 visits, and sorts by count descending, then name.
4. A score of 40 to 59 → WATCH, 0 seats.
5. **Error cases:** `sold_pct` outside 0..100, `tier` outside 1..3, `capacity` < 1 or `days_out` < 0 raises `ValueError`; the CLIs print `error: ...` and exit 1.
6. Georgian public holidays and their eves add +12 (e.g. Orthodox Easter 2026-04-12, and 2026-11-22 as the eve of Giorgoba).
7. `explain()` calls the model only for RESERVE. It returns the model's sentence only if it is one line, ≤ 40 words, and every number in it appears in the decision's facts; otherwise, or with no key, it returns the template.
8. Every model call, including failed ones, appends exactly one line to `logs/usage.jsonl` with `ts, feature, model, tokens_in, tokens_out, cost_usd, latency_ms, ok`.

## Context list
| Information | Where it lives |
|---|---|
| Weights, thresholds, holiday list | constants at the top of `src/reserve.py` |
| Model id, key, log path | environment: `FANRESERVE_MODEL`, `OPENROUTER_API_KEY`, `FANRESERVE_USAGE_LOG` (`.env.example`) |
| Prices | `PRICES` in `src/llm.py`, with the date they were read |
| Why things are the way they are | `docs/decisions/` |

## Constraints
No key in any file. Tests never call a real model. Every model call goes through `src/llm.py`. No personal data in `data/` or prompts.

## Napkin math
`decide()` costs $0. Operator reason: 50 RESERVE decisions a day × 30 = 1,500 calls a month × (≈ 250 tokens in × $0.825/M + ≈ 40 out × $4.125/M) ≈ **$0.56 a month** on `google/gemini-3.8-flash` (price read 2026-11-18). The prompt is short: the system line plus about eight lines of facts. HW1 assumed 600 / 150 tokens ($1.67). To be replaced by medians from `logs/usage.jsonl`.

## Out of scope (for now)
Payments, seat maps, a trained model, the fan-facing mobile UI, resale.

## Verification
`pytest` from the repo root: green means every test in `tests/` passes with `OPENROUTER_API_KEY` unset. CI runs the same command on every push and pull request.
