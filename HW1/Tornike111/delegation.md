# HW1 delegation log · Operator reason message

**Date:** 2026-11-18 · **Tool:** Claude, with the HW1 brief and our team repo as context · **Rung on the Autonomy Ladder:** 4 (the agent wrote the code and docs and checked its own work; I chose the feature and ran the tests)

**What I delegated.** I asked the agent to read the HW1 brief and our team repo and propose features. I picked the operator reason message from its three options and asked it to build `llm.py`, `explain.py`, the tests with a fake model, and drafts of `spec.md` and `golden.md`. Rule I set: the sentence may only restate the listed reasons.

**Plan check.** The agent proposed the feature and the shape (fallback template, no model call for WATCH/SKIP) before writing code. I chose the feature and approved the plan as proposed.

**What came back wrong.**
1. `llm.py` wrote the usage log to `logs/usage.jsonl` relative to the current folder. Run from the repo root, that creates `logs/` outside `hw1/Tornike111/`, so my PR would touch a file outside my folder. Caught by reading the diff against the submission rule; now it goes to `src/logs/`.
2. The napkin math assumed about 250 input tokens. Caught by measuring the real prompt (354 characters, about 100 tokens); the estimate went from $0.26 to $0.20 a month.
3. A bad decision file crashed the CLI with a full traceback. Caught by running the CLI on `examples/bad.json`; now it prints `error: ...` and exits 2 (criterion 5).
4. The grounding check only catches invented numbers, not invented words. Caught while writing golden question 2; not fixed, logged as a risk.

**How I verified.** I ran `pytest hw1/Tornike111` myself before pushing (green). The four problems above were caught by running the CLI, measuring the prompt, and checking the diff against the folder rule.

**Decision.** Fixed 1-3, kept 4 as a known risk. **AGENTS.md change:** none, this folder has no AGENTS.md; the line I would add is "logs and outputs stay inside your own hw1 folder". **Cost:** about one hour, no paid model calls.

**What I would change next time.** Stay on rung 3 for real: read the tests before the code. Write "every file stays in my folder" into the spec before delegating. The agent cannot follow a rule I did not write.
