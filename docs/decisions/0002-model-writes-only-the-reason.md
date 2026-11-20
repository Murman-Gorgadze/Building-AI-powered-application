# 0002 · The model writes only the operator's one-line reason

**Date:** Week 4 (decided), recorded 18 November 2026 · **Proposed by:** Murman Gorgadze · **Agreed by:** Tornike Varshalomidze, by approving the pull request that adds this file

**Context.** A list like `tier 1 event (+35); Friday is a busy day (+18); selling fast (+25)` is correct but slow to read when an operator approves dozens of holds a day. A model writes a better sentence, but a model can also invent a cause ("demand is up 40% on last season") that the score never used, and the operator would then approve a hold for a reason that does not exist.

**Decision.** `src/reason.py` sends the model only the decision's facts (action, score, seats, reasons) and asks for one sentence. `is_grounded()` rejects the sentence if it has more than one line, more than 40 words, or **any number that is not in those facts**. Rejected, missing (no key) or failed calls fall back to a plain template built from the same facts. Only RESERVE decisions call the model; WATCH and SKIP always use the template.

**Alternatives.** *Template only:* zero cost and zero risk, but harder to scan. It remains the fallback. *Let the model see the whole event and attendance data:* more fluent, but more to invent from and personal data in a prompt for no benefit. *A judge model to check grounding:* doubles the cost for a sentence a regex can check well enough today.

**Consequences.** The operator always gets a reason, with or without a model, and `decide()` never depends on the provider. The number check does not catch invented causes without numbers ("because of a derby"); the Week 11 golden set adds cases for that. Every model call is logged in `logs/usage.jsonl` with feature `operator_reason`.
