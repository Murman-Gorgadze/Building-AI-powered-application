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
- **Caught by:** calling the MCP server by hand; a mutation run (plain `MCPServer` → 5 failures); `git status` before committing.
- **Decision:** kept, pending review by Tornike on the pull request.
- **Cost:** two sessions; no paid model calls (the tests and the MCP run use no key).
