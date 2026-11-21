# HW1 spec · Operator reason message

*FanReserve · individual feature · one page. Run from the repo root: `pip install -r hw1/Tornike111/src/requirements.txt && pytest hw1/Tornike111` · Try it: `python hw1/Tornike111/src/explain.py hw1/Tornike111/src/examples/reserve.json --offline` · Live model (optional): `export OPENROUTER_API_KEY=...` and drop `--offline`.*

## Goal

When FanReserve's `decide()` says RESERVE, the operator must approve the seat hold. This feature turns the decision's `reasons` into **one short sentence** written by a model, and never lets that sentence state a number that is not in the decision.

## Users

The operator (ticketing manager) approving holds. They want the "why" in one line, and they must be able to trust it.

## Acceptance criteria

Input: decision JSON with `event_id`, `action`, `score`, `reserve_seats`, `reasons` (list of strings). Output: `{"text", "source": "model" | "fallback"}` or `null`.

1. RESERVE, and the model reply is one sentence (no line break, no second sentence), has ≤ 40 words, and every number in it appears in the decision → returns that sentence, `source = "model"`; the prompt contains every listed reason.
2. RESERVE, and the model sentence contains any number not in the decision → returns the template `Reserve <seats> seats for <id> (score <score>): <reasons joined by "; ">.`, `source = "fallback"`.
3. WATCH or SKIP → returns `null` and makes zero model calls.
4. Error: the model call raises (no key, network error) → template, `source = "fallback"`; CLI exit code 0.
5. Error: a missing field, empty `reasons` or unknown `action` → `ValueError`; CLI prints `error: ...` and exits 2. A missing file or invalid JSON → the same `error: ...` and exit 2, no traceback.
6. Cost and latency: every model call goes through `llm.py`, which appends `model, tokens_in, tokens_out, cost_usd, latency_s` (never the text) to `src/logs/usage.jsonl`. Tests make no network call.

## Context the agent needs

- Decision shape: `hw1/Murman-Gorgadze/src/reserve.py` (read only, not imported, so my folder runs on its own).
- `AGENTS.md` (repo root): keys from env only, log every model call.
- This file.

## Constraints

Python 3.11+, standard library only (pytest for tests). Key from `OPENROUTER_API_KEY`, model from `HW1_MODEL` (default `google/gemini-2.5-flash`). Every file stays inside `hw1/Tornike111/`.

## Out of scope

Calling `decide()`, any UI, retries or a fallback model, catching invented facts that contain no number.

## Napkin math

Prompt ≈ 350 characters ≈ 100 tokens in, ≈ 40 out. 50 RESERVE decisions a day × (100 × $0.30/M + 40 × $2.50/M) × 30 ≈ **$0.20 a month** (OpenRouter price for `google/gemini-2.5-flash`, checked 21 Nov 2026 from the OpenRouter models API). WATCH and SKIP cost nothing.

## Risks

The model adds a claim with no number ("always sells out") and the check misses it. The model swaps numbers that are both in the decision ("78% sold, score 85") and the check misses that too, because it only asks whether each number appears somewhere (golden question 4, a known fail). Mitigation now: the operator still sees the full reasons list in the decision; later: a per-claim check or a judge model.

## Verification

`pytest hw1/Tornike111` is green (16 tests: criteria 1-6, all with a fake model; plus 1 `xfail` test for the known limit in golden question 4). Golden questions in `golden.md` run from the CLI.
