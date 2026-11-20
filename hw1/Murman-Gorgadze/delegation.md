# HW1 delegation log · FanReserve "Reserve or Skip"

**Rung on the Autonomy Ladder:** 3, supervised task delegation. The agent drafts across several files; nothing is kept until the tests run and I have read the diff.

### Entry 1 · First draft of spec and code (October)
- **Task:** spec, `reserve.py`, three tests, golden, journal and delegation drafts from my product idea (loyalty reserve, weekday/holiday/tour demand).
- **Delegated to:** an AI chat agent, with the Lab 1 brief and templates as context.
- **Plan check:** none. I accepted the files as they came. That was the mistake.
- **Came back wrong:** the delegation log and journal were agent drafts full of `[fill this in]` brackets and I submitted them unchanged; the tests were weaker than the spec (see entry 2); the pushed branch held `.pyc` files and a stray `Z` at the top of this file.
- **Caught by:** the instructor's HW1 feedback, not by me. No gate of mine stood between the draft and the submission.

### Entry 2 · Fix after feedback (18 November 2026)
- **Task:** spec AC1 to AC6, a CLI, tests that fail when the feature breaks, real golden outputs.
- **Delegated to:** Claude Code (Opus 5.5), with the instructor's feedback, `Lab-3/MILESTONE-1.md` and the example in `Lab-3/examples/hw1-example/` as context.
- **Came back wrong / found:**
  1. The old test for golden 2 checked only `SKIP`, never the 0 seats the spec promises. A mutation that made SKIP hold 99 seats passed all 3 old tests. Two more mutations (no `sold_pct` check, no WATCH band) also passed. Fixed: new tests for seats, WATCH and `ValueError` (`golden.md`, mutation table).
  2. The napkin math used $0.30 in / $2.50 out per million tokens and called it the default model's price. The OpenRouter models list on 18 Nov gives `google/gemini-3.8-flash` at $0.825 / $4.125; $0.30 / $2.50 is `gemini-3.5-flash-lite`. Monthly estimate corrected from $0.83 to $1.67.
  3. The reason text says "selling fast" for any velocity above zero, even 1.5% a day (golden 2). Logged as a known weakness.
  4. The holiday list misses Georgian public holidays (for example 19 January, Orthodox Easter on 12 April, 28 August, 23 November). Not fixed inside HW1; it is fixed in the team copy `src/reserve.py`.
- **Caught by:** running the CLI and pasting real output; mutation runs in a scratch copy; reading the live price from `openrouter.ai/api/v1/models`.
- **Decision:** kept the fixes, kept the decision rule-based (team decision record `docs/decisions/0001`).

## One thing I rejected
Making `decide()` call a model to "estimate demand". It would cost money on every event, give a different answer on each run, and give the operator no reasons to check. The model only writes the explanation, and only later.

## What I would do differently
Write the error criteria and the WATCH case into the spec first, and read the tests before the code. The agent wrote tests for the happy path only because my spec only had happy-path criteria.
