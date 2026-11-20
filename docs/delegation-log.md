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
