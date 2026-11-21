# Pattern Journal · Tornike111 · Weeks 1 to 4

*One entry per week: the pattern, one place I saw or used it, one thing I would do differently. Written on 18 November 2026; the examples come from my HW1 feature.*

## Week 1 · Context as Budget

**Where I used it:** in HW1 I gave the agent only three things: the HW1 brief, our team repo, and the example folder. **What I noticed:** the second draft matched the required format because of the example; the right context did more than a longer prompt would have. **Do differently:** give the example at the start, not after the first draft.

## Week 2 · Spec Before Code

**Where I used it:** each acceptance criterion in my `spec.md` became one test, including two error cases. **What I noticed:** the rule "logs stay inside my folder" was not in the spec, and the first version broke it. **Do differently:** write the error cases and the folder rule into the spec before anything is built.

## Week 3 · Uncertainty-Aware UX

**Where I used it:** the fallback in `explain.py`. When the model's sentence cannot be trusted, or the call fails, the operator gets the plain list of reasons instead of a guess. **What I noticed:** a safe default is better than hiding that the model failed. **Do differently:** show the operator which one they got (`source: model` or `fallback`) in the UI too, not only in the JSON.

## Week 4 · Grounded Generation

**Where I used it:** the model may only restate the listed reasons. Golden question 2 has the model invent a 40 GEL price, and the check rejects the sentence. **What I noticed:** the check only looks at numbers, so "this match always sells out" still passes. **Do differently:** add a check per claim, or a judge model, so invented words are caught too.
