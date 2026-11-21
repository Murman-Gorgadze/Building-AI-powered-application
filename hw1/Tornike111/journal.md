# Pattern Journal · Tornike111 · Weeks 1 to 4

*One entry per week: the pattern, one place I saw or used it, one thing I would do differently. I wrote these late, after the weeks themselves, so every example comes from my HW1 work. First version 18 Nov 2026; each entry below is dated with the day it was last updated.*

## Week 1 · Context as Budget · updated 21 Nov 2026

**Where I used it:** the live runs measured my prompt at 116–129 tokens in, close to my estimate of 100, so the napkin math held. The surprise was the output side: reasoning models spent all 120, then all 1000, output tokens "thinking" and never wrote the sentence. **What I noticed:** thinking tokens are part of the budget and are billed as output; my worst case went from $0.21 to $3.81 a month. **Do differently:** measure with a live call on day one instead of estimating.

## Week 2 · Spec Before Code · updated 21 Nov 2026

**Where I used it:** each acceptance criterion in `spec.md` has a test. **What I noticed:** the spec promised "one sentence" and exit codes 0 and 2, but nothing checked them until the review on 21 Nov; a rule without a test is only a wish. **Do differently:** write the test name next to each criterion when I write the spec.

## Week 3 · Uncertainty-Aware UX · updated 21 Nov 2026

**Where I used it:** the fallback in `explain.py`. On 21 Nov a real `429 Too Many Requests` and an empty reasoning-model reply both ended in the plain template with exit 0, so the operator still got a true message. **What I noticed:** the fallback only stays safe if the failure is also logged; at first the empty reply crashed before logging. **Do differently:** show the operator whether the line came from the model or the template, not only in the JSON.

## Week 4 · Grounded Generation · updated 21 Nov 2026

**Where I used it:** the model may only restate the listed reasons, and any invented number sends the operator to the template (golden question 2). **What I noticed:** the check asks only whether each number appears somewhere, so swapped numbers ("78% sold, score 85") pass. That is golden question 4, a documented fail. **Do differently:** tie each number to the words around it, or add a judge model.
