# AI Playbook

The reusable, step-by-step method used to build and harden Task Tracker with AI
assistance while keeping ownership, correctness, and scope firmly with the human
author. This is the "how we work with AI" reference — a companion to
`docs/ai_usage_report.md` (what happened) and `docs/final-ai-review.md` (the final
sign-off). Future maintainers should follow this playbook for any AI-assisted change.

---

## Core principle

> **AI drafts; the human decides.** Treat every AI output as a proposal to be read,
> run, and break-tested — never as trusted code. A passing test suite is necessary but
> not sufficient, because an AI can write a test that agrees with its own wrong
> implementation.

---

## The loop (apply to every AI-assisted change)

```
1. FRAME     Write a strong prompt: role/context, task, constraints, output format.
2. GENERATE  Ask the AI for a draft of ONE layer at a time.
3. READ      Inspect the diff before running it — for correctness AND scope.
4. RUN       pytest tests/ -v  and  python -m tests.verify_a
5. BREAK     Deliberately break the rule; confirm the RIGHT test fails; restore.
6. DECIDE    Accept / edit / reject. Record non-obvious decisions.
7. DOCUMENT  Update docs only with claims verified against the code.
```

Never skip steps 3 and 5 — they are where real bugs are caught.

---

## 1. FRAME — how to prompt

Use the four-part shape (from the course prompt libraries):

- **Role / context:** e.g. "You are working in a FastAPI + Pydantic v2 Task Tracker
  with an in-memory store."
- **Task:** one concrete change, scoped to a single layer.
- **Constraints:** the guardrails — "no new dependencies," "no new endpoint," "compute,
  don't store," "keep server-managed fields out of input models."
- **Output format:** exactly which files/edits you want back.

**Weak → strong example** (from `docs/midcourse/prompt-log.md`):
- ❌ Weak: "Add due dates to my task tracker."
- ✅ Strong: "Add one optional `due_date` field to `TaskCreate`/`TaskUpdate`/
  `TaskResponse`; rely on Pydantic to reject malformed dates with 422; do **not** store
  an overdue flag — add `is_overdue(due_date, status, today=None)` where overdue means
  due date strictly before today AND status is not Done; output the exact edits to
  `models.py`, `storage.py`, `business_rules.py`."

A weak prompt produces work you cannot review against a clear intent. Fix the prompt,
not just the code.

---

## 2. GENERATE — one layer at a time

Generate per layer (model → storage → rule → endpoint → frontend → tests), not the
whole feature at once. Small drafts are reviewable; large ones hide bugs and scope
creep.

---

## 3. READ — the review checklist

Before running anything, check the draft for:

- **Correctness:** does the logic match the *intended* rule, not just a plausible one?
  (The `is_overdue` `Done`-exemption bug passed its own test — only reading caught it.)
- **Scope:** did the AI add an endpoint, field, dependency, or framework you did not
  ask for? Reject it. (Rejected here: a `/search` endpoint, client-only filtering,
  assignee search.)
- **Layering:** does anything import "up" the stack (models importing storage/main)?
- **Contract:** correct HTTP status codes (201/204/404/422)? Input vs output models
  kept separate? `extra="forbid"` preserved?
- **Security:** no secrets in source; user output escaped in the frontend; no
  loosening of validation or CORS.

---

## 4. RUN — verification commands

```bash
pytest tests/ -v          # full API suite (currently 37 passing)
python -m tests.verify_a  # 8 model checks
```

For endpoints, also run a live check (curl / Swagger UI at `/docs`) against a running
`uvicorn app.main:app --reload --port 8000`.

---

## 5. BREAK — the Break Test

For any rule you touched:

1. Copy the source file (throwaway copy).
2. Break the specific rule (e.g. remove an exemption, invert a comparison).
3. Run `pytest` and confirm the **specific** protecting test fails.
4. Restore the file; confirm the suite is green again.

If breaking the rule does **not** fail a test, your tests are not protecting the
behavior — add a test before accepting the change. Proven Break Tests for this repo are
listed in `docs/release-evidence.md` §3.

---

## 6. DECIDE — accept / edit / reject, and record it

- **Accept** only after READ + RUN + BREAK pass.
- **Edit** when the draft is close but wrong in a detail (e.g. debounce search at
  250 ms instead of firing per keystroke; pin relative test dates to constants).
- **Reject** out-of-scope or unsafe suggestions, and write down why.

Keep a short record of non-obvious decisions (the prompt log is the model:
`docs/midcourse/prompt-log.md`).

---

## 7. DOCUMENT — verify before you assert

Only state something in the docs after confirming it in the source (and, for behavior,
in a passing test). During this project a documented "XSS action item" was corrected to
a "strength" after reading the frontend showed `escapeHtml()` already covers every user
field. Verify, don't assume.

---

## Scope guardrails (do NOT let AI cross these without human confirmation)

| Change | Rule |
|--------|------|
| New product feature | Not without an explicit request |
| Change a status code / transition rule / overdue definition | Human confirmation required |
| Data-model change | Human confirmation required |
| New runtime dependency | Human confirmation required |
| Add auth / persistence / a framework | Human confirmation required (out of current scope) |
| Loosen validation or CORS | Reject unless explicitly required |
| Rewrite git history / flatten the repo layout | Not without an explicit request |

Safe-by-default AI work: adding tests, adding/expanding docs, CI, Docker, and
`.gitignore`/`.env.example` hygiene that keeps the suite green.

---

## Red flags that mean "stop and review harder"

- The AI's change also rewrote the test that would have caught it.
- A "small" fix touches multiple layers at once.
- New imports, endpoints, fields, or dependencies appear unrequested.
- A doc claim you cannot immediately point to in the source.
- The suite goes green only after a test was weakened or deleted.

---

## One-line summary

**Frame it tightly, generate small, read before you run, break it to trust it, reject
scope creep, and only document what you verified.** That is how AI stayed an assistant
on this project and ownership stayed with the human author.
