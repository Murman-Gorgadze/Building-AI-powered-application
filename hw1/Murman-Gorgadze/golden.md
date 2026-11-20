# HW1 golden questions · FanReserve "Reserve or Skip"

Run on 18 November 2026 from the repo root, Python 3.14, no network, no key. The CLI is `python hw1/Murman-Gorgadze/src/reserve.py`; every question is also a test in `src/test_golden.py` (`pytest hw1/Murman-Gorgadze`: 10 passed).

| # | Question (input) | Expected | Actual (pasted from the run) | Pass? | How I ran it |
|---|---|---|---|---|---|
| 1 | Football, tier 1, Fri 2026-10-23, capacity 50,000, 85% sold, 21 days out | RESERVE, score 78, 5,000 seats | `RESERVE score=78 seats=5000` · reasons: tier 1 event (+35), Friday is a busy day (+18), selling fast, 85% sold 21d out (+25) | pass | `--tier 1 --day 2026-10-23 --capacity 50000 --sold 85 --days-out 21`; `test_g1_big_friday_football_reserves` |
| 2 | Football, tier 3, Tue 2026-10-27, capacity 8,000, 30% sold, 20 days out | SKIP, 0 seats | `SKIP score=15 seats=0` · reason: selling fast, 30% sold 20d out (+15) | pass | `--tier 3 --day 2026-10-27 --capacity 8000 --sold 30 --days-out 20`; `test_g2_minor_tuesday_skips` |
| 3 | Fans on 2026-10-07: ana 4 football visits in September; beka 1 football + 3 concerts; gio 5 football visits on 2026-03-01 (outside 90 days). Category football | only ana, count 4 | `[('ana', 4)]` | pass | `rank_fans(att, "football", date(2026, 10, 7))` from a Python prompt; `test_g3_fan_ranking_uses_category_and_window` |

## Extra checks (not one of the three)

| Input | Expected | Actual | Pass? |
|---|---|---|---|
| Concert tour stop, tier 2, Wed 2026-10-14 (holiday), capacity 12,000, 55% sold, 14 days out, `--tour` | RESERVE, 600 seats (5%) | `RESERVE score=68 seats=600` · tier +18, Wednesday +3, holiday +12, tour +10, selling fast +25 | pass |
| Same as #1 with `--sold 150` (adversarial) | `ValueError`, exit 1 | `error: sold_pct must be 0..100`, exit 1 | pass |
| Tier 2, Sat 2026-10-24, capacity 3,000, 10% sold, 20 days out | WATCH, score 45, 0 seats | `WATCH`, 45, 0 (test only) | pass |

## Do the tests catch a broken feature?

I broke the code on purpose in a scratch copy and ran both the old 3 tests and the new 10.

| Mutation | Old tests (3) | New tests (10) |
|---|---|---|
| remove the `sold_pct` range check | 3 passed: **missed** | 3 failed |
| remove the WATCH band (40 → 60) | 3 passed: **missed** | 1 failed |
| SKIP holds 99 seats instead of 0 | 3 passed: **missed** | 1 failed (g2 now checks seats) |
| tier 1 holds 5% instead of 10% | 1 failed | 2 failed |
| ignore the 90-day window | 1 failed | 1 failed |

## Known weaknesses

- Golden 2 shows the reason text "selling fast" for 1.5% a day. Any velocity above zero is labelled "selling fast"; the wording should depend on the size of the term. Logged, not fixed in HW1.
- Sell-through is capped at +25, so a tier 3 Thursday event that sells out in a day still scores 8 + 25 = 33 and is SKIPped.
- Thresholds 60/40 and all weights are untuned guesses until a backtest on real past events runs.
