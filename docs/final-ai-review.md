# Final AI Review

A closing, whole-repository review of AI-assisted work before final submission. This
document satisfies **Part C** with two graded mini-logs (an AI *code* review and an AI
*security* review of real files), a confirmation that the `AGENTS.md` guardrails were
followed, my three AI-usage rules, and a first-person ownership statement.

- **Reviewer:** the repository author (final gate)
- **Date:** 2026-08-10
- **Branch:** `final-project`
- **Verdict:** ✅ Approved for submission — AI output was reviewed and graded, not
  trusted blindly.

Companion documents: `docs/code_review.md` (code quality), `docs/security_review.md`
(full security analysis), `docs/ai_usage_report.md` (governance narrative),
`docs/ai-playbook.md` (my working method), `docs/release-evidence.md` (objective proof).

---

## Part C.1 — AI Code Review Mini-Log

**What I did:** I asked an AI assistant to review the real, submitted source file
[`app/main.py`](../app/main.py) and return specific comments. Below are its actual
comments, each **graded (Useful / Noise / Wrong)** with my reasoning and the action I
took. This grades the *AI's output*, not my code.

| # | AI comment (on `app/main.py`) | Grade | My reason | Action taken |
|---|-------------------------------|-------|-----------|--------------|
| 1 | "`allow_origin_regex` combined with `allow_methods=['*']` and `allow_headers=['*']` (lines 32–34) is very permissive; scope it before any deployment." | **Useful** | Accurate and actionable. The wildcard methods/headers are safe only because the origin regex is localhost-only. It matches an independently-reached conclusion in the security review. | Recorded as a pre-deployment gate in `docs/security_review.md`; left as-is for local scope (intended). |
| 2 | "In `list_tasks`, a blank `q` (`q.strip()` falsy, line 73) silently returns all tasks; consider rejecting blank `q` with a 422 for consistency." | **Wrong** | This misreads the contract. Blank/absent `q` means *no search filter*, which must return the full (other-filtered) list — returning 422 would break `GET /tasks` and several passing tests. | Rejected. No change. Noted the reasoning here so it is not re-raised. |
| 3 | "Filters in `list_tasks` are applied as sequential list comprehensions (lines 67–78), each O(n); combine them into a single pass for efficiency." | **Noise** | Technically true but irrelevant at this scope: the store is a small in-memory dict, and clarity beats a micro-optimization here. Documented as tech debt (W4) already. | No change. Cross-referenced `docs/code_review.md` (W4). |
| 4 | "The storage `ValidationError` → `RequestValidationError` remap (lines 118–121) is good, but consider logging the error so failures are observable." | **Useful** | Fair: the remap prevents a 500, but the failure is currently silent. Logging is a reasonable, in-scope hardening idea. | Deferred (out of this submission's no-behavior-change rule); logged as a future item in `docs/code_review.md` tech-debt notes. |

**Summary:** 4 AI comments — 2 Useful, 1 Noise, 1 Wrong. Two were acted on
(documented / deferred), one rejected with reasoning, one dismissed as negligible. The
AI did not surface a real defect, which is consistent with the code being covered by
37 passing tests.

---

## Part C.2 — AI Security Mini-Review

**What I did:** I asked an AI assistant to review the repository for security issues
with file evidence. Below are its findings, each **graded (Valid / False Positive /
Noise)** with the evidence I checked and the **next action**.

| # | AI finding | File evidence | Grade | Reason | Next action |
|---|-----------|---------------|-------|--------|-------------|
| 1 | "No authentication on any endpoint — anyone can read, modify, or delete every task." | `app/main.py` (all routes; no auth dependency) | **Valid** | True and by design for the local single-user scope; it is the top gate before deployment. | Documented as mandatory pre-deployment gate in `docs/security_review.md` §4. Do not expose the API on a network until auth is added. |
| 2 | "CORS allows any `localhost`/`127.0.0.1` origin on any port with `*` methods/headers." | `app/main.py:32-34` | **Valid** | Correct; safe locally, unsafe if deployed. | Replace the regex with an explicit origin allow-list before deployment (`docs/security_review.md` §5). No change for local scope. |
| 3 | "Frontend renders task cards with `innerHTML` (`frontend/index.html:473`) → stored-XSS risk from task text." | `frontend/index.html:473` vs `escapeHtml` at `:383`, used at `:478,480,484,490,493` | **False Positive** | The `innerHTML` template interpolates only values already passed through `escapeHtml()`. Every user field (title, description, assignee, due_date, priority) is escaped. | No code change. Keep the escaping invariant on any future card field; recorded in `docs/security_review.md` §3. |
| 4 | "`python-dotenv` is a dependency, so secrets in `.env` may leak into version control." | `requirements.txt`; `.gitignore`; `.env.example` | **Noise** | `.env` is git-ignored, only the non-sensitive `.env.example` is committed, no secret exists, and dotenv is not even read at runtime. The finding is generic, not evidence-based here. | None. Documented that the project stores no secrets (`docs/security_review.md` §1). |

**Summary:** 4 findings — 2 Valid (both already documented as pre-deployment gates),
1 False Positive (disproved by reading the source), 1 Noise. The two Valid findings
are accepted risks for the local scope and blockers for any public deployment; neither
changes the local-scope verdict.

---

## Manual security check

Separate from the AI-assisted review above, I performed my **own manual** security
check — no AI involved — by reading the source and repository state directly. This is
what I looked at and what I found:

1. **Secret scan of source and git history.** I searched the codebase and history for
   credentials:
   ```bash
   grep -ri "password\|secret\|api_key\|apikey\|token\|authorization" app/ frontend/ tests/
   git log -p -- .env            # any committed .env content?
   git ls-files | grep -E "\.env$|\.pem$|\.key$"
   ```
   **Result:** no secrets, tokens, keys, or credentials in source or history. `.env` is
   git-ignored; only the non-sensitive `.env.example` is tracked. **Pass.**

2. **Input-boundary check.** I confirmed by reading `app/models.py` that every input
   model uses `extra="forbid"` (blocking mass-assignment of `id`/timestamps) and that
   `app/storage.py` re-validates the merged record before committing, so a rejected
   update surfaces as 422 and cannot corrupt the store. **Pass.**

3. **Frontend output-escaping check.** I traced `renderCard` in
   `frontend/index.html` and confirmed every user-supplied field (title, description,
   assignee, due_date, priority) is wrapped in `escapeHtml()` before it reaches the
   `innerHTML` template (`:383` definition, used at `:478,480,484,490,493`). **Pass.**

4. **Trust-boundary check.** I confirmed the API has **no authentication** and that
   CORS (`app/main.py:32-34`) is limited to localhost origins. **Finding:** acceptable
   for the local single-user scope, but both are hard gates before any deployment.
   **Next action:** documented in `docs/security_review.md` §4–§5; do not expose the
   API publicly until auth + an explicit CORS allow-list are added.

**Manual-check verdict:** no secrets, strong input validation, safe output escaping;
the only real exposure (no auth / permissive CORS) is a known, documented,
scope-appropriate acceptance.

---

## One AI output I rejected or corrected

A dedicated record of AI output I did **not** simply accept. (There were several; two
representative cases below — one rejected, one corrected.)

### Rejected — a new `/search` endpoint

- **What the AI proposed:** while building the search feature, the assistant suggested
  adding a dedicated `POST /search` (and, separately, filtering the already-loaded task
  list only in the browser).
- **Why I rejected it:** a new endpoint was out of the Module scope, and client-only
  filtering would have left the backend search **untested and unenforced**. Both were
  the wrong shape for this project.
- **What I did instead:** I extended the existing `GET /tasks` with a `q` query
  parameter (case-insensitive substring over title/description), combined with the
  existing filters, and had the frontend call that endpoint. This keeps filtering
  enforced and tested on the backend. Evidence: `app/main.py:73-78`,
  `tests/test_midcourse.py` search tests.

### Corrected — the `is_overdue` rule flagged completed tasks

- **What the AI produced:** the first `is_overdue` draft treated **any** task with a
  past due date as overdue — including tasks already marked `Done` — and it wrote a test
  that agreed with that flawed behavior, so the suite passed.
- **How I caught it:** by **reading the draft**, not from a failing test. A finished
  task is not late, so the logic was wrong even though it was green.
- **What I did:** I added the `status is TaskStatus.Done` exemption
  (`app/business_rules.py:51`) and wrote `test_completed_task_is_not_overdue` to lock
  the correct behavior in, then proved it with a Break Test (removing the exemption
  makes that test fail). This is the clearest example of why I treat a passing suite as
  necessary but not sufficient.

---

## Part C.3 — AGENTS.md guardrail confirmation & AI-usage rules

**Guardrail confirmation.** I confirm the guardrails defined in
[`AGENTS.md`](../AGENTS.md) were followed throughout the hardening work:

- ✅ **No product features or business-rule changes** were made (the hard constraint).
- ✅ **No source files** in `app/`, `frontend/`, or `tests/` were modified — hardening
  added only docs, CI, Docker, and hygiene files.
- ✅ **Layering, HTTP status codes, and the data contract** were left intact.
- ✅ **Test suite stayed green** (`37 passed`, `8/8` model checks) before and after.
- ✅ **No secrets** were introduced; `.env` remains git-ignored.

**My three AI-usage rules (enforced on this project):**

1. **Never-paste rule.** I never paste secrets, credentials, tokens, `.env` contents,
   production logs, or personal/customer data into an AI prompt or tool. AI sees only
   non-sensitive source and docs. (This project contains no secrets, so there was
   nothing sensitive to withhold — the rule still governs how I work.)
2. **Draft-not-authority rule.** AI output is a draft to be read, run, and break-tested
   before acceptance. A passing suite is never sufficient proof on its own, because an
   AI can write a test that agrees with its own wrong implementation.
3. **Scope-lock rule.** I reject any AI suggestion that adds a feature, endpoint,
   dependency, or framework I did not ask for, and I record the rejection. Scope is
   mine to set, not the assistant's.

---

## Part C.4 — Ownership statement (first person)

I am comfortable submitting this repository as my own work. I set the scope and made
every acceptance decision myself: I read each AI-generated file before keeping it, I
re-ran the full test suite (`37 passed`) and the model checks (`8/8`) to confirm the
results with my own eyes, and I graded the AI's code and security comments above rather
than taking them on faith — accepting the useful ones, rejecting the wrong one, and
disproving a false-positive by reading the source. When the AI was wrong earlier in the
project (the `is_overdue` bug that flagged completed tasks as overdue), I caught it,
fixed it, and locked the fix in with a regression test, and I rejected out-of-scope
suggestions like a separate `/search` endpoint. I understand how every layer of this
system works, why each decision was made, and what its limitations are, and I can
maintain and extend it without AI assistance.

**Final sign-off:** approved for course submission.
