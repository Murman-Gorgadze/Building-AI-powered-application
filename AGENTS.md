# AGENTS.md · FanReserve
Decides which events hold seats back for loyal fans, how many and why, for ticketing operators. Spec: docs/spec.md

## Commands
install:  pip install -r requirements.txt
run:      python -m src.reason --tier 1 --day 2026-10-23 --capacity 50000 --sold 85 --days-out 21
test:     pytest            (product, tests/) · pytest hw1   (homework folders)
tools:    python -m src.act "<question>" [--operator op-1]   (function calling, needs a key)
mcp:      FANRESERVE_OPERATOR=op-1 python -m src.mcp_server   (MCP over stdio, no key)

## Conventions
- Model: `FANRESERVE_MODEL`, default `google/gemini-3.8-flash`, via OpenRouter.
- Every model call goes through `src/llm.py` and appends one line to `logs/usage.jsonl` (tokens, cost, latency, ok).
- `decide()` never calls a model (docs/decisions/0001). The model only writes the operator reason and may only restate `decide()`'s facts (0002).
- Weights, thresholds and the holiday list are constants at the top of `src/reserve.py`; no magic numbers in logic.
- Dates are `datetime.date`, ISO `YYYY-MM-DD` on the CLI; weekday Mon=0. Percentages are 0..100, not 0..1.
- Bad input raises `ValueError` with a message naming the field; CLIs print `error: ...` to stderr and exit 1.
- Every feature ships with a test and writes a log line when it runs (Evidence Rule). Tests use a fake model.

## Always
- Run `pytest` before saying you are done, and paste the result.
- Write a decision record in docs/decisions/ for any choice a newcomer would question.

## Ask first
- Adding a dependency
- Changing the `Decision` fields or a CLI's output shape
- Editing CI configuration (.github/)

## Never
- Read or write .env, or print a key
- Delete, skip, or weaken a test to make it pass
- Let a model change a decision, a seat count or a hold: those come from code and the operator
- Edit someone else's hw1/ or hw2/ folder
