# Handoff for Tornike · HW1 and team repo · 20 November 2026

Written by Murman (with Claude Code) so you can catch up from GitHub alone. Read it top to bottom once (about 10 minutes). Then follow the order in section 5, which starts with merging my PR #1.

---

## 1 · The situation in five lines

1. HW1 ("Spec to Ship") is **individual**: each of us has our own folder `hw1/<github-username>/` and our own grade. The professor gave you **0/5** and asked you to do your HW1 yourself in `hw1/Tornike111/`.
2. You already opened **PR #2** with your HW1 (operator reason message). It is almost complete, but it is in the wrong folder (`HW1/`, capital letters). Section 3A fixes that.
3. My HW1 fixes are in **PR #1**. The team files the professor asked for (contract, spec, decisions, `src/`, tests, CI) are in **PR #3**.
4. The professor's rule: **one person opens a PR, the other reviews and merges.** So you review and merge my PRs #1 and #3, and I review and merge your PR #2. Nobody merges their own PR.
5. HW2 is **not started on purpose**. We finish HW1 first.

## 2 · Where everything is

| What | Link / path | Who acts |
|---|---|---|
| Your HW1 | PR #2 · branch `hw1-Tornike111` · folder `HW1/Tornike111/` (must become `hw1/Tornike111/`) | **you** fix it, I review and merge |
| My HW1 fixes | PR #1 · branch `hw1-Murman-Gorgadze` · folder `hw1/Murman-Gorgadze/` | **you** review and merge |
| Team foundation | PR #3 · branch `team-foundation` (built on top of PR #1) | **you** review and merge, after PR #1 |
| HW1 brief | course repo `Lab-1/HOMEWORK.md`, `Lab-3/MILESTONE-1.md`, `Lab-4/HOMEWORK.md` | read |
| Team contract | `TEAM-CONTRACT.md` (in PR #3) | **you** sign it (3C) |
| How the product works | `README.md`, `docs/spec.md`, `docs/decisions/0001`–`0003` (in PR #3) | read |
| Model usage evidence | `logs/usage.jsonl` (in PR #3): the first live model calls, 20 Nov, OpenRouter free models | read |

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

## 3 · What you must do, in this order

### 3A · Fix your HW1 (PR #2): about 30 minutes

**First merge my PR #1** (3B, step 1). Your fix starts from `main` *after* that merge. Otherwise the rename below would also move my old `HW1/Murman-Gorgadze/` folder into your pull request.

I checked out your branch and ran it on 20 Nov. **The good news:** all four files and `src/` are there, `pytest HW1/Tornike111` gives **10 passed**, and the CLI works (`--offline` prints the fallback sentence). **The problems:**

| # | Problem | Why it matters | Fix |
|---|---|---|---|
| 1 | **The folder is `HW1/Tornike111/`, not `hw1/Tornike111/`.** | GitHub and Linux treat `HW1` and `hw1` as different folders. The brief says `hw1/`, and the CI job runs `pytest hw1`, which finds **0 of your tests**. The grader may not find your folder. I had the same mistake: PR #1 moves my folder from `HW1/` to `hw1/`. | Rename it (commands below). |
| 2 | Paths inside your docs say `HW1/...`, including `HW1/Murman-Gorgadze/src/reserve.py` and `HW1/Murman-Gorgadze/AGENTS.md`. They were right on `main` when you wrote them, but PR #1 moves my folder to `hw1/Murman-Gorgadze/` and `AGENTS.md` to the repo root. | After the merge, a reviewer who copies your run commands gets "file not found". | Change `HW1/` to `hw1/` everywhere, and point to `AGENTS.md` at the **repo root**. |
| 3 | Your `delegation.md` says you ran `pytest hw1/Tornike111`. With the old folder name, that command finds no tests. | An honest log has to match what really happened. | After the rename, run it, and make sure the sentence is true. |
| 4 | Napkin math says the $0.30 / $2.50 per million tokens for `google/gemini-2.5-flash` is "an assumption". | I checked on 20 Nov: OpenRouter's live list gives exactly **$0.30 / $2.50** for that model, so your numbers are right. An unchecked price still loses points. | Run the command below yourself, then replace "an assumption" with "OpenRouter price, read on <date>". |
| 5 | The PR description is empty. | The reviewer (me) and the professor read it first. | Two lines: what the feature is, and how to run the tests. |

**Commands.** Run them in your clone of the team repo:

```bash
git fetch origin
git switch hw1-Tornike111
git pull
git merge origin/main        # brings in PR #1 (my folder is now hw1/Murman-Gorgadze/)

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
pytest hw1                   # 20 passed: my 10 and your 10 (tested on a copy of your branch on 20 Nov)

# 4 · the live price, for the napkin math (on 20 Nov it printed 0.0000003 0.0000025)
curl -s https://openrouter.ai/api/v1/models | python -c "import json,sys; [print(m['id'], m['pricing']['prompt'], m['pricing']['completion']) for m in json.load(sys.stdin)['data'] if m['id']=='google/gemini-2.5-flash']"
# the numbers are USD per token: multiply by 1,000,000 for the price per million

git add -A hw1/Tornike111
git status                   # every change must be inside hw1/Tornike111/
git commit -m "HW1 Tornike111: move to hw1/, fix paths and price"
git push
```

Then edit the PR #2 description on GitHub, and post a comment like "fixed, ready for review".

**Optional but strong evidence: one live model call.** All your golden questions use a fake model. OpenRouter has free models, so one real call costs nothing. Make a key at openrouter.ai → Keys (no credit needed; copy the key right away, because it is shown only once). Then:

```bash
read -s OPENROUTER_API_KEY && export OPENROUTER_API_KEY      # paste the key, press Enter (nothing shows)
export HW1_MODEL=google/gemma-4-31b-it:free
python hw1/Tornike111/src/explain.py hw1/Tornike111/src/examples/reserve.json
```

If you get error 429, the free model is busy: retry, or try `google/gemma-4-26b-a4b-it:free` or `nvidia/nemotron-3.5-lightning:free`. If it works, add the result as a fourth row in `golden.md`, saying it was a live run, and commit `src/logs/usage.jsonl`. **Never commit or paste the key itself.**

**Before you submit, read every file and every line of code in your folder.** The course rule: *"Submitting output you cannot explain is misconduct, and oral defense of any work can be required."* If a sentence in `journal.md` or `delegation.md` is not what you would say, rewrite it in your own words.

**Submit:** after I merge PR #2, fill the HW1 submission form on Teams with the link to `hw1/Tornike111/` on `main`. The deadline was 20 October, so **email the professor first** (zeshan.ahmad@kiu.edu.ge) and ask whether a late resubmission is accepted.

### 3B · Review and merge my PRs: about 20 minutes

1. **PR #1 first** (my HW1).
   - Open "Files changed". Check that the changes are inside my HW1 folder. You will see `HW1/Murman-Gorgadze/` deleted and `hw1/Murman-Gorgadze/` added: that is the same rename you are making. One exception: `AGENTS.md` moved from my folder to the repo root, because it is the team's file.
   - Optional: `git switch hw1-Murman-Gorgadze && pytest hw1/Murman-Gorgadze` (10 passed).
   - Click **Review changes → Approve**, then **Squash and merge**, then **Delete branch**.
2. **Then PR #3** (team foundation). When the HW1 branch is deleted, GitHub moves PR #3 so it targets `main` (check that the base says `main`).
   - Read `TEAM-CONTRACT.md`, `docs/spec.md`, `docs/decisions/`, `src/`, and section 6 of `docs/DESIGN-REVIEW.md`. **The roles and the meeting time in the contract are a proposal.** If you disagree, write a review comment *before* approving.
   - Run it:
     ```bash
     git switch team-foundation && pip install -r requirements.txt
     pytest -q tests && pytest -q hw1
     python -m src.reason --tier 1 --day 2026-10-23 --capacity 50000 --sold 85 --days-out 21
     ```
   - Approve, **Squash and merge**, delete the branch.
3. Tell me when both are merged. I then tag the revised Design Review (`design-review-v2`); the professor said the old tag pointed at the wrong commit.

### 3C · Sign the team contract: 5 minutes, after PR #3 is merged

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

- HW1 (`hw1/Murman-Gorgadze/`): fixed everything from the Milestone 1 feedback. Removed the committed `.pyc` files and the stray "Z", added run commands and an error criterion to the spec, raised the tests from 3 to 10, wrote real outputs in `golden.md`, and rewrote `delegation.md` and `journal.md`. **PR #1**
- Team repo (**PR #3**): `TEAM-CONTRACT.md`, `docs/spec.md`, decisions 0001–0003, `src/reserve.py`, `src/llm.py` (every model call is logged), `src/reason.py`, 29 tests, CI, the revised Design Review.
- First real model calls on 20 Nov: 7 lines in `logs/usage.jsonl` (6 refused because the free model was busy, 1 success: 158 tokens in, 120 out, 1.6 s). Design Review section 5 now uses those numbers.
- Will do: review and merge your PR #2, merge your contract signature, tag `design-review-v2`, fill my own HW1 form.

## 5 · Who does what, at a glance

| # | Task | Who | Waits for |
|---|---|---|---|
| 1 | Review and merge PR #1 | Tornike | nothing |
| 2 | Fix PR #2 (merge `main`, rename to `hw1/`, paths, price date, description) | Tornike | #1 in this table |
| 3 | Review and merge PR #3 | Tornike | #1 in this table |
| 4 | Review and merge PR #2 | Murman | #2 in this table |
| 5 | Sign `TEAM-CONTRACT.md` from your account | Tornike | #3 |
| 6 | Tag `design-review-v2` | Murman | #3 |
| 7 | Email the professor: team confirmation, and late HW1 for Tornike | both | nothing |
| 8 | HW1 forms on Teams | each of us | own PR merged |

Questions: write to me on Teams. Disagree with anything here? Comment on PR #3. That is where the team decisions are reviewed.
