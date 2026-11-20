# 0003 · Every model call goes through `src/llm.py` and OpenRouter

**Date:** 18 November 2026 · **Proposed by:** Murman Gorgadze · **Agreed by:** Tornike Varshalomidze, by approving the pull request that adds this file

**Context.** The course gives us one OpenRouter key, prices change during the semester (the default model's price on 18 November was not the one in our first napkin math), and the Evidence Rule says every feature ships with a test and a log entry.

**Decision.** `src/llm.py` is the only module that imports a model client. It uses the OpenAI SDK pointed at OpenRouter, reads `OPENROUTER_API_KEY` and `FANRESERVE_MODEL` (default `google/gemini-3.8-flash`) from the environment, and writes one JSON line per call to `logs/usage.jsonl`: time, feature, model, tokens in and out, cost, latency, ok. Failed calls are logged too, with `ok: false`.

**Alternatives.** Each provider's own SDK: one code path per provider. Logging through Python `logging` only: nothing durable to compute medians from for the Design Review.

**Consequences.** One place to change models, add a fallback chain (Week 10) or a cap on calls. Tests replace `llm.client` with a fake and point the log at a temp file, so CI never needs a key. The price table in `llm.py` must be re-read from OpenRouter whenever we quote a cost.
