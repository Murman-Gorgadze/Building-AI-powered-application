# Spec · FanReserve: "Reserve or Skip" decision engine

## Problem
Fans who attend the same kind of event every week get shut out when a big event sells out. I hold a reserve of tickets to reward them, but holding seats back is expensive, so I must know exactly which events deserve a reserve and which do not.

## Users
- **Operator (me / ticketing manager):** decides each day which upcoming events get a reserve and how many seats.
- **Loyal fans:** people who attended at least 3 events of the same category (e.g. football) in the last 90 days and want first access to a related big event (e.g. Champions League).

## Success criteria
1. On a backtest of ≥50 past events, RESERVE decisions are correct (event sold out or ≥95% full) at least 75% of the time.
2. At least 80% of reserved seats end up bought by ranked loyal fans (low waste).
3. Each decision returns in under 200 ms and lists the reasons behind its score.

## Core feature (Weeks 2 to 4 scope)
`decide(event)` returns RESERVE, WATCH, or SKIP, a 0 to 100 demand score, the number of seats to hold, and plain-language reasons. The score combines event tier, weekday (Fri/Sat/Sun busiest), holiday or holiday eve, tour stop, and sell-through speed. `rank_fans()` then orders eligible fans by how often they attended that category in the last 90 days.

## Context list
| Information | Where it lives |
|---|---|
| Event: category, tier, date, capacity, % sold, days until event, tour flag | Events table / CSV |
| Holiday calendar | Config list in `reserve.py` (must be verified) |
| Fan attendance history (category, date) | Attendance table / CSV |
| Weights and thresholds | Constants at top of `reserve.py` |

## Acceptance criteria
1. A Friday tier-1 event that is 85% sold 21 days out returns RESERVE with 10% of capacity.
2. A minor Tuesday event that is 30% sold returns SKIP with 0 seats.
3. Fan ranking counts only the requested category and only the last 90 days, most frequent first.

## Napkin math
Optional LLM layer that turns reasons into a one-line message for the operator, for RESERVE decisions only.
50 requests/day × (600 tokens in × $0.30/M + 150 tokens out × $2.50/M) × 30 ≈ **$0.83 / month** on the default model.
*Prices are my assumption; check the current OpenRouter price before relying on this.* The scoring itself costs nothing.

## Risks and safety
- Hand-set weights may not match real demand → tune on the backtest; the reasons list makes wrong decisions easy to spot.
- Holiday list is incomplete or wrong → treated as config, verified before launch.
- Misuse: a scalper creating many fake "loyal fan" accounts → require ticket-scan attendance proof and a per-fan purchase cap.

## Out of scope (for now)
Payments, seat maps, a trained ML model (this version is rule-based and explainable), the fan-facing mobile UI, resale.
