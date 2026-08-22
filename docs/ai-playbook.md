# AI Playbook

My personal, first-person policy for working with AI on this repository and beyond.
It has six sections: when I reach for AI first, when I do not, my non-negotiables, my
review rules, what I am still figuring out, and a Decision Card I can apply in the
moment. Companion documents: `docs/ai_usage_report.md` (what happened) and
`docs/final-ai-review.md` (the graded final review).

---

## 1. When I reach for AI first

I go to AI first when the task is well-defined, low-risk, and easy for me to verify:

- **Scaffolding and boilerplate** — a Dockerfile, a CI workflow, a test skeleton, a
  docstring pass. I can read the result in full and I have a suite to check it.
- **Drafting documentation** from facts I already know, then verifying each claim
  against the code (as I did for every file in `docs/`).
- **Generating test cases** for behavior I can state precisely (e.g. "valid due date →
  201, malformed → 422"), because a wrong test is cheap to spot and cheaper to break-test.
- **Explaining or exploring** an unfamiliar API, error, or library before I commit to a
  design — using AI as a fast reference I then confirm.
- **A second-opinion review pass** over a real file, where I grade its comments (see
  `docs/final-ai-review.md`) rather than adopt them wholesale.

The common thread: **I can verify the output quickly and the blast radius is small.**

---

## 2. When I do NOT reach for AI first

I do the thinking myself first when getting it wrong is expensive or the AI can't see
what matters:

- **Scope and requirements decisions** — what to build, what to reject. AI repeatedly
  proposed out-of-scope work here (a `/search` endpoint, client-only filtering,
  assignee search); those are my calls, not its.
- **Business rules and their edge cases** — the status lifecycle and the overdue
  definition. The AI's first `is_overdue` draft was subtly wrong; I need to own that
  logic, not outsource it.
- **Security and trust boundaries** — auth, CORS, what counts as a secret. I decide the
  policy; AI can only flag candidates.
- **Anything involving real secrets or data** — I never hand those to an AI at all
  (see non-negotiables).
- **Architecture that others will depend on** — layering and the data contract, where a
  plausible-but-wrong suggestion would ripple across the whole codebase.

The common thread: **if a wrong answer is hard to detect or hard to undo, I lead and
use AI only to pressure-test my own reasoning.**

---

## 3. My non-negotiables

These do not bend, regardless of deadline or convenience:

- **Never paste secrets, credentials, tokens, `.env` contents, production logs, or
  personal/customer data into an AI prompt or tool.** Ever.
- **No AI change ships without me reading the full diff.** No blind "apply all."
- **The test suite must be green before and after** — I never weaken or delete a test to
  make a change pass.
- **No new product feature, dependency, endpoint, or framework** enters via AI without
  my explicit intent.
- **Every documented claim must be verified against the source** before I write it down.
- **I own the result.** If it's in my repo, I can explain it and maintain it without AI.

---

## 4. My review rules

How I actually review AI output before accepting it:

- **Read for correctness AND scope.** Does the logic match the *intended* rule, not just
  a plausible one? Did it quietly add something I didn't ask for?
- **Run it:** `pytest tests/ -v` and `python -m tests.verify_a`; live-check endpoints
  against a running server for API changes.
- **Break-test any rule I touched:** break the source, confirm the *specific* protecting
  test fails, then restore. If nothing fails, the tests aren't protecting the behavior —
  I add a test before accepting.
- **Grade the AI, don't just consume it.** For review comments, I label each
  Useful / Noise / Wrong (or Valid / False Positive / Noise for security) with a reason,
  so I decide deliberately (see `docs/final-ai-review.md`).
- **Distrust green.** A passing suite can be an AI test agreeing with an AI bug; the
  Break Test is what turns "passes" into "protects."
- **Record non-obvious decisions** so I (or a teammate) don't re-litigate them.

---

## 5. What I am still figuring out

Honest open questions I haven't fully settled:

- **How much to pin dependencies.** Lower-bound pins keep installs simple but hurt
  reproducibility; I lean toward a committed lockfile but haven't adopted one here yet
  (`docs/dependency_review.md`).
- **When AI-generated tests are "enough."** They cover the happy path well; I'm still
  calibrating how aggressively to add adversarial and unit-level cases beyond the API.
- **Where to draw the line on AI-suggested refactors.** Some (the `Storage` class,
  single-pass filtering) are reasonable but out of scope now — I'm working out when
  "nice" becomes "worth the churn."
- **Trusting AI security findings.** This round produced 2 valid, 1 false positive, 1
  noise. I don't yet have a reliable prior for how much manual verification each finding
  needs before I act.
- **Prompt discipline.** I still sometimes start too broad and have to rewrite the
  prompt tighter; recognizing that earlier is a skill I'm building.

---

## 6. The Decision Card

A quick check I run *before* accepting any AI-assisted change:

```
DECISION CARD — apply before accepting AI output
────────────────────────────────────────────────
1. Did I paste anything sensitive?        → If yes, STOP. Never do this.
2. Have I read the entire diff?           → If no, read it fully first.
3. Is it in scope (no new feature/dep)?   → If no, reject or ask myself why.
4. Does it match the INTENDED rule?       → Not just "plausible" — the real contract.
5. Did I run the suite + verify script?   → 37 passed / 8-of-8 must hold.
6. Did I break-test any rule I touched?   → Right test must fail, then restore.
7. Are my doc claims verified in source?  → No unverified assertions.
8. Can I explain and maintain this alone? → If no, I don't own it yet — dig in.

If all 8 pass → ACCEPT and record the decision.
If any fail  → EDIT, REJECT, or investigate before proceeding.
```

**One line:** *Never paste secrets, read everything, keep scope, break-test to trust,
verify before I write it, and only ship what I can own.*
