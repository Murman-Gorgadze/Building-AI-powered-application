# Golden questions

Run with: `python -m pytest -q` (3 passed). Scores below are from running the code.

| # | Input | Expected | Actual | Result |
|---|---|---|---|---|
| 1 | Football, tier 1, Fri 2026-10-23, capacity 50,000, 85% sold 21 days out | RESERVE, 5,000 seats | RESERVE, score 78, 5,000 seats (tier +35, Friday +18, velocity +25) | PASS |
| 2 | Football, tier 3, Tue 2026-10-27, capacity 8,000, 30% sold 20 days out | SKIP, 0 seats | SKIP, score 15, 0 seats | PASS |
| 3 | Fans: ana has 4 football visits in window; beka has 1 football + 3 concerts; gio has 5 football visits but 6+ months old. Category = football | Only ana, count 4 | `[("ana", 4)]` | PASS |

## Extra check (not one of the three)
Concert tour stop, tier 2, Wed 2026-10-14 (a holiday), 55% sold 14 days out → RESERVE, score 68, 600 seats. The holiday and tour points pushed a midweek show over the threshold, which is the behavior I wanted.

## Known weakness
The sell-through term is capped at +25, so a tier-3 event that sells out extremely fast still scores low. I have not tested real data, so the thresholds (60/40) are untuned guesses.
