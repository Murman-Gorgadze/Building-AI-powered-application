# 0001 · `decide()` is a rule-based score, not a model

**Date:** Week 2 (decided), recorded 18 November 2026 · **Proposed by:** Murman Gorgadze · **Agreed by:** Tornike Varshalomidze, by approving the pull request that adds this file

**Context.** Holding seats back for loyal fans is a money decision: a seat held for an event that would have sold anyway is lost revenue, and a seat not held for a sell-out shuts a loyal fan out. The operator has to trust the decision and be able to argue with it. We have no historical sales data yet to train or evaluate a learned model.

**Decision.** `decide()` in `src/reserve.py` is a weighted sum of named signals (tier, weekday, holiday or holiday eve, tour stop, sell-through speed) with thresholds RESERVE ≥ 60 and WATCH ≥ 40. Every weight is a constant at the top of the file, and every point appears in the `reasons` list. It makes no model call.

**Alternatives.** *Ask a model for a demand estimate:* costs tokens on every event, can give a different answer on each run, and its "reasons" are a story rather than the actual computation. *Train a regression model:* the right step once we have at least 50 past events with sales curves, but not before; it would also need its own evaluation set.

**Consequences.** Decisions are free, take microseconds, are repeatable (the same event always gives the same answer) and are testable with exact values (`tests/test_reserve.py`). The weights are hand-set guesses: we will watch the backtest (success criterion S1 in `docs/spec.md`) and tune them there. The interface `Event -> Decision` stays fixed, so a learned scorer can replace `demand_score()` later without touching callers.
