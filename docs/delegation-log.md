# Delegation log · FanReserve

One entry per delegation that mattered. HW1's own log is `hw1/Murman-Gorgadze/delegation.md`.

### Entry 1 · Team repo foundation and operator reason
- **Task:** the instructor's Milestone 1 follow-up: `TEAM-CONTRACT.md`, `docs/spec.md`, decisions 0001 to 0003, `src/llm.py` with a usage log, `src/reason.py` (spec AC7, AC8), and the Design Review placeholders.
- **Delegated to:** Claude Code (Opus 5.5), rung 3. Context: the instructor's feedback email, the course repo (`Lab-2` templates, `Lab-3/MILESTONE-1.md`, `Lab-4/templates/DESIGN-REVIEW.md`), this repo. Date: 18 November 2026.
- **Plan check:** the agent proposed building the HW1 fixes and the team files on two separate branches, so the HW1 pull request only touches `hw1/Murman-Gorgadze/`. Approved.
- **Came back wrong / found:**
  1. The old Design Review and spec priced the default model at $0.30 / $2.50 per million tokens. OpenRouter's models list on 18 November gives `google/gemini-3.8-flash` at $0.825 / $4.125. Corrected everywhere; `PRICES` in `llm.py` carries the date.
  2. The `HOLIDAYS_2026` sample missed most Georgian public holidays (Orthodox Easter, 19 January, 12 and 17 May, 28 August, 23 November). Extended in `src/reserve.py` and marked as written from the agent's knowledge: **still to be checked against matsne.gov.ge**.
  3. The reason text said "selling fast" for 1.5% a day. Now "steady sales" below +20 (`test_ac2_slow_sales_are_not_called_fast`).
  4. The agent created `.github/workflows/ci.yml` and added `openai` to `requirements.txt`, although the old AGENTS.md said not to touch CI and to ask before adding a dependency. Flagged in the pull request for the repo keeper to accept or revert.
- **Caught by:** running the CLIs; mutation runs; reading the live price; the AGENTS.md rules.
- **Decision:** kept, pending review by Tornike on the pull request.
- **AGENTS.md change:** v2. Commands, the "decide() never calls a model" rule, and "Ask first: editing CI configuration".
- **Cost:** one session; no paid model calls by the tests.

### Entry 2 · HW2 tool frame and `check_reserve` (Murman-Gorgadze)
- **Task:** HW2 product work: wrap `decide()` as the tool `check_reserve` (contract, registry, function-calling loop, MCP server), 7 golden cases in `evals/tools/Murman-Gorgadze.yaml`, `docs/tool-contracts.md`.
- **Delegated to:** Claude Code (Opus 5.5), rung 3. Context: `Lab-5/HOMEWORK.md`, `Lab-5/examples/campuspulse-tools/`, `Lab-7/HOMEWORK.md`, `Lab-8/templates/hw2-writeup.md`, this repo. First draft 20 November (parked), finished 25 November 2026.
- **Plan check:** the agent asked before every push, pull request and settings change; the journal lines were left for me to write.
- **Came back wrong / found:**
  1. Through the MCP door, the SDK silently dropped an extra `action: RESERVE` argument and ran the tool, and for `sold_pct: 150` it sent pydantic's raw error with a link to its docs. Found by calling the server by hand. Fixed: our contract is checked before the SDK's (`docs/decisions/0004`); 5 new tests in `tests/test_mcp.py` fail on the plain server.
  2. Refusals said only what was wrong. They now say what to do next (Lab 7), and the unknown-tool message lists the tools the caller can use.
  3. A manual run wrote `logs/tools.jsonl` into the repo. Deleted, and the file is now in `.gitignore`.
  4. The branch adds `pydantic`, `pyyaml` and `mcp` to `requirements.txt`. AGENTS.md says to ask first: asked, approved by me on 25 November.
  5. Found by Tornike in review, on Windows: `test_both_doors_send_the_same_refusal` failed with `pydantic` 2.13, which lists two errors in a different order on each door. CI (2.14) and my machine passed. Fixed by sorting the errors by field in `invalid_arguments()`; checked green on 2.12, 2.13 and 2.14.
- **Caught by:** calling the MCP server by hand; a mutation run (plain `MCPServer` → 5 failures); `git status` before committing; Tornike running `pytest` on his own machine.
- **Decision:** kept, pending review by Tornike on the pull request.
- **Cost:** two sessions; no paid model calls (the tests and the MCP run use no key).

### Entry 3 · HW2 `rank_loyal_fans` (Tornike111)
- **Task:** HW2 product work: wrap `rank_fans()` as the operator-only tool `rank_loyal_fans` on Murman's frame (contract, registry entry, MCP registration), made-up `data/attendance.json`, 5 golden cases in `evals/tools/Tornike111.yaml`, `tests/test_rank_loyal_fans.py`, `docs/tool-contracts.md` section, `docs/decisions/0005`.
- **Delegated to:** Claude Code (Opus 5.5), rung 3. Context: `Lab-5/HOMEWORK.md`, `Lab-5/templates/`, `Lab-8/HOMEWORK.md`, PR #9, this repo. Date: 25 November 2026.
- **Plan check:** the agent laid out the plan and the file list before writing; I create the branches, commits and pull requests myself, the agent only writes code.
- **Came back wrong / found:**
  1. The MCP door lists every tool to every client, so it cannot hide an operator-only tool the way `tools_for(None)` does. Kept Murman's "same tools through both doors" test; the MCP tool refuses at call time when the server has no `FANRESERVE_OPERATOR`. Written down as a known limit in `docs/tool-contracts.md`.
  2. `rank_fans()` had the loyalty rule as default arguments (90, 3). Moved to constants `LOYAL_WINDOW_DAYS` and `LOYAL_MIN_VISITS` at the top of `src/reserve.py` (AGENTS.md: no magic numbers), and left them out of the contract so the model cannot lower the bar (`docs/decisions/0005`).
- **Caught by:** mutation runs before committing: `operator_only=False` fails golden case `Tornike111:a1` and 3 other tests; dropping `extra="forbid"` fails 8 tests in `tests/test_rank_loyal_fans.py`.
- **Decision:** kept, pending review by Murman on the pull request.
- **Cost:** one session; no paid model calls (tests and golden cases use no key).

### Entry 4 · Lab 5 team tool `check_day`
- **Task:** catch up Lab 5: a team tool different from both HW2 tools, its contract, tests, MCP registration, golden cases, the two AGENTS.md lines, the Week 5 journal entry.
- **Delegated to:** Claude Code (Opus 5.5), rung 3. Context: `Lab-5/README.md`, `docs/tool-contracts.md`, this repo. Date: 25 November 2026. I chose the capability ("is this date busy?"); the agent chose the design.
- **Plan check:** the agent asked before every push, pull request and setup change.
- **Came back wrong / found:**
  1. A copy of the weekday and holiday rules inside the tool would have been able to drift from `decide()`. Instead the rules moved into `day_points()` in `src/reserve.py`, used by both; `test_agrees_with_the_scoring_rules` checks they match.
  2. Two tests listed the exact tools offered (`test_act.py`); they were updated to include `check_day`, not loosened.
- **Caught by:** `pytest` (141 product tests), reading the diff.
- **Decision:** kept, pending review by Tornike on the pull request.
- **Cost:** one session; no paid model calls.
