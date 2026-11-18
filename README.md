# FanReserve

**Decides which upcoming events should hold seats back for loyal fans, how many, and why.**
CS6920 capstone · Fall 2026 · MG-TV · Murman Gorgadze, Tornike Varshalomidze

> Status: Week 9 (midterm period) · `decide()` and the grounded operator reason work and are tested. The tool contract, fan Q&A, ticket-photo attendance and operator agent are planned (`docs/spec.md`, Slices).

## The problem
Fans who go to the same kind of event every week lose out when a big event sells out. Organisers can hold a reserve for them, but every held seat is unsold revenue if the event would have sold anyway. Today that choice is made by gut feeling.

## Run it
```
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
pytest
python -m src.reason --tier 1 --day 2026-10-23 --capacity 50000 --sold 85 --days-out 21
```
For a model-written reason, export `OPENROUTER_API_KEY` in your shell first (never in a file). Without it, the template reason is printed.

## How it works
`src/reserve.py` scores an event from tier, weekday, holiday, tour stop and sell-through speed, then returns RESERVE / WATCH / SKIP, the seats to hold and the reasons. No model is involved. `src/reason.py` asks a model, through `src/llm.py`, to turn those reasons into one sentence, and throws the sentence away if it contains any number the decision did not produce. Key decisions: [docs/decisions/](docs/decisions/)

## Does it work? (evidence)
| What we measure | Result | Where |
|---|---|---|
| Unit tests | 29 passing, no key needed | `tests/`, CI |
| HW1 golden questions | 3 / 3 pass, plus 3 extra checks | `hw1/Murman-Gorgadze/golden.md` |
| Golden set (model features) | planned for HW2 week | `evals/` |
| Cost per request | see log | `logs/usage.jsonl` |

## Team and how we work
Murman Gorgadze (repo and spec keeper) · Tornike Varshalomidze (eval keeper) · Team rules: [docs/TEAM-REPO.md](docs/TEAM-REPO.md) · Spec: [docs/spec.md](docs/spec.md) · Delegation log: [docs/delegation-log.md](docs/delegation-log.md) · Journals: [docs/journal/](docs/journal/) · Team contract: [TEAM-CONTRACT.md](TEAM-CONTRACT.md) · Design Review: [docs/DESIGN-REVIEW.md](docs/DESIGN-REVIEW.md)
