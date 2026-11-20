# Spec · FanReserve: "Reserve or Skip" decision engine

*HW1 · Murman-Gorgadze · one page. From a fresh clone, at the repo root:*
*Install: `pip install pytest` (Python 3.11+, no other dependency) · Test: `pytest hw1/Murman-Gorgadze` · Try it: `python hw1/Murman-Gorgadze/src/reserve.py --tier 1 --day 2026-10-23 --capacity 50000 --sold 85 --days-out 21`*

## Problem
Fans who attend the same kind of event every week get shut out when a big event sells out. An organiser can hold a reserve of tickets for them, but every held seat is unsold revenue if the event would have sold anyway. The operator must know which events deserve a reserve, how many seats, and why.

## Users
- **Operator (ticketing manager):** decides each day which upcoming events get a reserve and how many seats.
- **Loyal fans:** attended at least 3 events of one category (e.g. football) in the last 90 days.

## Feature
`decide(event)` returns RESERVE, WATCH or SKIP, a 0 to 100 demand score, the seats to hold and a list of reasons. The score adds points for tier (1: +35, 2: +18), weekday (Fri +18, Sat +22, Sun +15, Thu +8, Wed +3), holiday or holiday eve (+12), tour stop (+10) and sell-through speed (% sold per day × 10, capped at +25). RESERVE at ≥ 60, WATCH at 40 to 59, SKIP below 40. RESERVE holds 10% of capacity for tier 1 and 5% otherwise, rounded up. `rank_fans()` orders eligible fans by visits to the requested category in the last 90 days. No model call, no network.

## Acceptance criteria (each is a test in `src/test_golden.py`)
1. Tier 1, Friday 2026-10-23, capacity 50,000, 85% sold, 21 days out → `RESERVE`, score 78, 5,000 seats.
2. Tier 3, Tuesday 2026-10-27, capacity 8,000, 30% sold, 20 days out → `SKIP`, 0 seats.
3. `rank_fans(attendance, "football", today)` counts only football visits dated in `[today − 90 days, today]`, keeps fans with ≥ 3, sorts by count descending, then name.
4. A score of 40 to 59 returns `WATCH` with 0 seats (tier 2, Saturday 2026-10-24, 10% sold, 20 days out → score 45).
5. **Error case:** `sold_pct` outside 0..100 (e.g. 150) or `tier` outside 1..3 raises `ValueError`; the CLI prints `error: ...` to stderr and exits 1.
6. `decide()` returns in under 200 ms (pure arithmetic; measured in microseconds).

## Context list
| Information | Where it lives |
|---|---|
| Weights and thresholds | constants at the top of `src/reserve.py` |
| Holiday calendar | `HOLIDAYS_2026` in `src/reserve.py` (a sample; see Risks) |
| Event fields | the `Event` dataclass: category, tier, day, capacity, sold_pct, days_out, is_tour |
| Fan attendance | a dict `fan -> [(category, date)]` passed to `rank_fans()` |

## Napkin math
The decision costs nothing: no model. A later optional model call writes a one-line reason for the operator, for RESERVE only: 50 a day × 30 = 1,500 calls a month × (600 tokens in × $0.825/M + 150 out × $4.125/M) ≈ **$1.67 a month** on `google/gemini-3.8-flash` (OpenRouter price read on 2026-11-18; my first draft used $0.30/$2.50, which was wrong).

## Risks
- Weights are hand-set guesses, not learned → the reasons list makes a wrong decision visible; tune on a backtest of past events.
- Holiday list is a sample and incomplete → treat as config and verify against the official calendar before use.
- Scalpers farming "loyal fan" status → attendance must come from ticket-scan proof, plus a per-fan purchase cap.

## Out of scope
Payments, seat maps, a trained model, any model call, the fan-facing UI, resale, reading data from files or a database.
