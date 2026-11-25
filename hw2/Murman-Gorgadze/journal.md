# HW2 · Pattern Journal · Murman-Gorgadze · Weeks 5, 6, 7

*Written on 25 November 2026, after the weeks themselves, from my answers about the HW2 work. The Lab 6 and Lab 7 code was not built in our repo; the Week 6 and Week 7 entries say what FanReserve should do and point at the code that exists.*

### Week 5 · Tool Contract
**Where I used it:** `check_reserve`, contract class `CheckReserve` in `src/contracts.py`, product pull request #9. **What I noticed:** CI was green and the tests passed on my computer, but on Tornike's computer `tests/test_mcp.py::test_both_doors_send_the_same_refusal` failed, because his setup had a different `pydantic` version. The automatic checks alone did not catch it; a teammate on a different computer did (fixed in commit `df87a33`). **Do differently:** ask my teammate to run the tests on his computer early, and test on more than one setup before I say the work is done.

### Week 6 · Session State
**Where I used it:** not built yet. FanReserve should remember the events an operator is watching, for that operator only, for at least one year, and nothing about fans. **What I noticed:** `check_reserve` remembers nothing between calls, which is why it gives the same answer twice (see `contract.md`, "Idempotent?"); memory will need its own rules about who it belongs to and when it is deleted. **Do differently:** do the labs in order, on time, so this entry has real code and a real test behind it.

### Week 7 · Supervised Autonomy Loop
**Where I used it:** the loop in `src/act.py`, which stops after 3 model turns (`MAX_ROUNDS = 3`). There is no tool that places a hold: placing a seat hold is the one action that must wait for the operator's yes, and the AI may only suggest it. **What I noticed:** `check_reserve` only reads, so it does not need anyone's yes; only actions that change something do. **Do differently:** start earlier, so the approval step for holds is built and tested before the deadline instead of only described.
