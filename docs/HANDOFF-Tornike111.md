# Handoff for Tornike · HW1 and team repo · 20 November 2026 (updated after the merges)

Written by Murman (with Claude Code) so you can catch up from GitHub alone. Read it top to bottom once (about 10 minutes). Then follow the order in section 5.

---

## 1 · The situation in six lines

1. HW1 ("Spec to Ship") is **individual**: each of us has our own folder `hw1/<github-username>/` and our own grade. The professor gave you **0/5** and asked you to do your HW1 yourself in `hw1/Tornike111/`.
2. Your HW1 (**PR #2**, the operator reason message) is **merged into `main`**. It is almost complete, but it sits in the wrong folder, `HW1/Tornike111/` (capital letters). Section 3A fixes that with one small new PR.
3. My HW1 fixes (**PR #1**) and the team files the professor asked for (**PR #3**: contract, spec, decisions, `src/`, tests, CI) are also merged into `main`. CI is green.
4. **Mistake to own:** on 20 Nov I merged all three PRs myself, including yours, with no review. The professor's rule is that **one person opens a PR and the other reviews and merges.** Section 3B is how we repair that, and from now on we follow the rule.
5. HW2 is **not started on purpose**. We finish HW1 first.
6. Everything below was checked on a copy of `main` on 20 Nov: product tests 29 passed, my HW1 10 passed, your HW1 10 passed.

## 2 · Where everything is (all on `main`)

| What | Path | Who acts |
|---|---|---|
| Your HW1 | `HW1/Tornike111/` (must become `hw1/Tornike111/`) | **you** fix it in a new PR (3A); I review and merge |
| My HW1 | `hw1/Murman-Gorgadze/` | **you** review it after the fact (3B) |
| Team files | `TEAM-CONTRACT.md`, `README.md`, `AGENTS.md`, `docs/`, `src/`, `tests/`, `.github/workflows/ci.yml` | **you** review (3B); sign the contract (3C) |
| How the product works | `README.md`, `docs/spec.md`, `docs/decisions/0001`–`0003` | read |
| Model usage evidence | `logs/usage.jsonl`: the first live model calls, 20 Nov, OpenRouter free models | read |
| HW1 brief | course repo `Lab-1/HOMEWORK.md`, `Lab-3/MILESTONE-1.md`, `Lab-4/HOMEWORK.md` | read |

**The HW1 folder must contain** (`Lab-4/HOMEWORK.md`):

```
hw1/<your-github-username>/
├── spec.md          one page: goal, users, acceptance criteria, context list, out of scope
├── golden.md        3 golden questions: question · expected · actual · pass or fail · how you ran it
├── delegation.md    half a page: what you delegated, what came back wrong, how you caught it
├── journal.md       Pattern Journal entries for Weeks 1, 2, 3 and 4
└── src/             the working feature, with at least one test that runs with `pytest hw1/<username>`
```

Grading: correctness 40 · code quality 20 · documentation and journal 20 · verification evidence 20.

## 3 · What you must do

### 3A · Fix your HW1 folder (new PR): about 30 minutes

I ran your HW1 on 20 Nov. **The good news:** all four files and `src/` are there, `pytest HW1/Tornike111` gives **10 passed**, and the CLI works (`--offline` prints the fallback sentence). **The problems:**

| # | Problem | Why it matters | Fix |
|---|---|---|---|
| 1 | **The folder is `HW1/Tornike111/`, not `hw1/Tornike111/`.** | GitHub and Linux treat `HW1` and `hw1` as different folders. The brief says `hw1/`, and the CI job runs `pytest hw1`, which finds **none of your tests**. The grader may not find your folder. I had the same mistake; PR #1 moved my folder to `hw1/`. | Move it (commands below). |
| 2 | Paths inside your docs say `HW1/...`, including `HW1/Murman-Gorgadze/src/reserve.py` and `HW1/Murman-Gorgadze/AGENTS.md`. They were right when you wrote them, but PR #1 moved my folder to `hw1/Murman-Gorgadze/` and `AGENTS.md` to the repo root. | A reviewer who copies your run commands gets "file not found". | Change `HW1/` to `hw1/` everywhere, and point to `AGENTS.md` at the **repo root**. |
| 3 | Your `delegation.md` says you ran `pytest hw1/Tornike111`. With the old folder name, that command finds no tests. | An honest log has to match what really happened. | After the move, run it, and make sure the sentence is true. |
| 4 | Napkin math says the $0.30 / $2.50 per million tokens for `google/gemini-2.5-flash` is "an assumption". | I checked on 20 Nov: OpenRouter's live list gives exactly **$0.30 / $2.50** for that model, so your numbers are right. An unchecked price still loses points. | Run the command below yourself, then replace "an assumption" with "OpenRouter price, read on <date>". |
| 5 | The PR #2 description was empty. | The reviewer and the professor read it first. | Write two lines in the new PR: what the feature is, and how to run the tests. |

**Commands.** Run them in your clone of the team repo:

```bash
git switch main
git pull
git switch -c fix-hw1-Tornike111

# 1 · move ONLY your folder (two steps, so it also works on Windows and macOS, which ignore case)
git mv HW1/Tornike111 tornike-tmp
git mv tornike-tmp hw1/Tornike111
git status                   # every line must be a rename HW1/Tornike111/... -> hw1/Tornike111/...

# 2 · find every old path that is left
grep -rn "HW1/" hw1/Tornike111
# fix each line: HW1/ -> hw1/, and HW1/Murman-Gorgadze/AGENTS.md -> AGENTS.md (repo root)

# 3 · run your tests the way the brief and CI do
pip install -r hw1/Tornike111/src/requirements.txt
pytest hw1/Tornike111        # must say 10 passed
pytest hw1                   # 20 passed: my 10 and your 10 (tested on a copy of main on 20 Nov)

# 4 · the live price, for the napkin math (on 20 Nov it printed 0.0000003 0.0000025)
curl -s https://openrouter.ai/api/v1/models | python -c "import json,sys; [print(m['id'], m['pricing']['prompt'], m['pricing']['completion']) for m in json.load(sys.stdin)['data'] if m['id']=='google/gemini-2.5-flash']"
# the numbers are USD per token: multiply by 1,000,000 for the price per million

git add -A hw1/Tornike111
git status                   # every change must be inside hw1/Tornike111/ (or the old HW1/Tornike111/)
git commit -m "HW1 Tornike111: move to hw1/, fix paths and price"
git push -u origin fix-hw1-Tornike111
gh pr create --title "HW1 Tornike111: move folder to hw1/" --body "Moves my HW1 to hw1/Tornike111/ so CI runs it; fixes paths and the price note. Run: pytest hw1/Tornike111"
# (or open the pull request on github.com)
```

**Do not merge it yourself.** I review and merge it.

**Optional but strong evidence: one live model call.** All your golden questions use a fake model. OpenRouter has free models, so one real call costs nothing. Make a key at openrouter.ai → Keys (no credit needed; copy the key right away, because it is shown only once). Then:

```bash
read -s OPENROUTER_API_KEY && export OPENROUTER_API_KEY      # paste the key, press Enter (nothing shows)
export HW1_MODEL=google/gemma-4-31b-it:free
python hw1/Tornike111/src/explain.py hw1/Tornike111/src/examples/reserve.json
```

If you get error 429, the free model is busy: retry, or try `google/gemma-4-26b-a4b-it:free` or `nvidia/nemotron-3.5-lightning:free`. If it works, add the result as a fourth row in `golden.md`, saying it was a live run, and commit `src/logs/usage.jsonl`. **Never commit or paste the key itself.**

**Before you submit, read every file and every line of code in your folder.** The course rule: *"Submitting output you cannot explain is misconduct, and oral defense of any work can be required."* If a sentence in `journal.md` or `delegation.md` is not what you would say, rewrite it in your own words.

**Submit:** after your fix PR is merged, fill the HW1 submission form on Teams with the link to `hw1/Tornike111/` on `main`. The deadline was 20 October, so **email the professor first** (zeshan.ahmad@kiu.edu.ge) and ask whether a late resubmission is accepted.

### 3B · Review my merged work: about 20 minutes

PRs #1 and #3 were merged without your review. You can no longer approve a merged PR, but you can still review it and leave a comment. That comment is the record that the review happened.

1. **PR #1** (my HW1): open it on GitHub, then "Files changed". Check that the changes stay inside my HW1 folder. You will see `HW1/Murman-Gorgadze/` deleted and `hw1/Murman-Gorgadze/` added: the same move you are making. One exception: `AGENTS.md` moved from my folder to the repo root, because it is the team's file.
2. **PR #3** (team files): read `TEAM-CONTRACT.md`, `docs/spec.md`, `docs/decisions/`, `src/`, and section 6 of `docs/DESIGN-REVIEW.md`. **The roles and the meeting time in the contract are a proposal.** If you disagree, say so in the comment and I will change them in a new PR.
3. Run it on `main`:
   ```bash
   git switch main && git pull && pip install -r requirements.txt
   pytest -q tests && pytest -q hw1
   python -m src.reason --tier 1 --day 2026-10-23 --capacity 50000 --sold 85 --days-out 21
   ```
4. On each PR, leave a comment such as: "Reviewed after merge on <date>: ran the tests (N passed), checked the folder rule, OK" (or list what is wrong).

### 3C · Sign the team contract: 5 minutes

The professor wants a commit **from your own GitHub account**:

```bash
git switch main && git pull
git switch -c docs-sign-contract
# in TEAM-CONTRACT.md, last line: replace ____ with your initials (TV) and today's date
git commit -am "Sign team contract (Tornike111)"
git push -u origin docs-sign-contract
gh pr create --title "Sign team contract" --body "Tornike's signature"   # or open the PR on github.com
```

I review and merge it.

### 3D · Reply to the professor's email

He asked **both of us** to reply to his email and confirm the team (MG-TV). Each of us replies separately.

## 4 · What Murman did (my half)

- HW1 (`hw1/Murman-Gorgadze/`, **PR #1**): fixed everything from the Milestone 1 feedback. Removed the committed `.pyc` files and the stray "Z", added run commands and an error criterion to the spec, raised the tests from 3 to 10, wrote real outputs in `golden.md`, and rewrote `delegation.md` and `journal.md`.
- Team repo (**PR #3**): `TEAM-CONTRACT.md`, `docs/spec.md`, decisions 0001–0003, `src/reserve.py`, `src/llm.py` (every model call is logged), `src/reason.py`, 29 tests, CI, the revised Design Review.
- First real model calls on 20 Nov: 7 lines in `logs/usage.jsonl` (6 refused because the free model was busy, 1 success: 158 tokens in, 120 out, 1.6 s). Design Review section 5 now uses those numbers.
- Will do: review and merge your fix PR and your contract signature, tag `design-review-v2`, fill my own HW1 form.

## 5 · Who does what, at a glance

| # | Task | Who | Waits for |
|---|---|---|---|
| 1 | Open the fix PR for your HW1 (move to `hw1/`, paths, price date, description) | Tornike | nothing |
| 2 | Review and merge that PR | Murman | #1 in this table |
| 3 | Review PRs #1 and #3 after the fact, and leave a comment on each | Tornike | nothing |
| 4 | Sign `TEAM-CONTRACT.md` from your account (new PR) | Tornike | nothing |
| 5 | Review and merge the signature PR | Murman | #4 |
| 6 | Tag `design-review-v2` | Murman | nothing |
| 7 | Email the professor: team confirmation, and late HW1 for Tornike | both | nothing |
| 8 | HW1 forms on Teams | each of us | own HW1 on `main` |

**From now on:** whoever opens a PR never merges it; the other person reviews, approves, and merges.

Questions: write to me on Teams.
