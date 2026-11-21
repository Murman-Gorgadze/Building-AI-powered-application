# HW1 delegation log · Operator reason message

**Sessions:** 18 Nov 2026 (build) and 21 Nov 2026 (review and fixes) · **Tool:** Claude, with the HW1 brief and our team repo as context · **Rung on the Autonomy Ladder:** 4. The agent wrote the code, tests and doc drafts; I chose the feature, ran every test, CLI command and live call myself, and made every commit from my own account.

**What I delegated.** 18 Nov: I asked the agent to read the brief and our repo and propose features, picked the operator reason message, and had it build `llm.py`, `explain.py`, the tests with a fake model, and drafts of `spec.md` and `golden.md`. My rule: the sentence may only restate the listed reasons. 21 Nov: I asked it to review the whole folder against the brief and fix what it found, one step at a time, explaining each change before making it.

**What came back wrong, and how it was caught.**

1. 18 Nov: the usage log was written outside my folder, and a bad decision file crashed the CLI. Caught by reading the diff and running the CLI on `bad.json`. Fixed.
2. The folder was `HW1/`, not `hw1/`, so CI found none of my tests. Caught by Murman's handoff and the professor's feedback. Fixed with `git mv` in two steps.
3. The spec promised "one sentence", but the check only counted words; a missing file still crashed the CLI; exit codes were not tested. Caught by the 21 Nov review. Fixed, with 6 new tests.
4. The number check accepts swapped numbers ("78% sold, score 85"). Caught by the review. **Not fixed**: golden question 4, an `xfail` test.
5. A live call to a reasoning model returned no text, and `llm.py` crashed **before logging the call**. Caught by my live run. Fixed: log first, then raise a clear error.
6. `max_tokens=120` was too small: the free models used all of it "thinking" (`finish_reason: length`). Caught by `usage.jsonl`. Raised to 1000.
7. A test failed only because `HW1_MODEL` was set in my terminal. Caught by running pytest after the live runs. Fixed by naming the model in the test.
8. My own mistake: a Find and Replace without Match Case changed "HW1" to "hw1" in text and in `HW1_MODEL`. Caught with `git diff`; restored and redone path by path.

**How I verified.** `pytest hw1/Tornike111`: 18 passed, 1 xfailed. CLI runs for exit codes 0 and 2. Live calls on 21 Nov, logged in `src/logs/usage.jsonl` (details in `golden.md`). Price read from the OpenRouter models API.

**Next time.** Do a live run on day one: it found two bugs no fake-model test could. Put the folder rule and "one sentence" checks into the spec before delegating. Read every diff before committing.
