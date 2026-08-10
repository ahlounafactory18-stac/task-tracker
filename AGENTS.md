# AGENTS.md

Guidance for AI agents and future human maintainers working on **Task Tracker**.
Read this before making changes. It explains what the project is, how it is built,
the rules you must not break, and the common workflows.

> **Golden rule:** this is a scoped learning project. Do **not** add product features
> or change business requirements unless explicitly asked. Most valuable work here is
> hardening: tests, docs, CI, hygiene — not new functionality.

---

## 1. Project purpose

A small full-stack task tracker for the AUB AI-Assisted Coding course. A team member
manages a single shared task list on a Kanban board, with a controlled status
lifecycle, optional due dates + overdue flagging, and search/filter. Backend is the
authority for all rules. Storage is in-memory (no database) by design. Full context:
`docs/project_overview.md`.

---

## 2. Architecture (what to know before editing)

Backend layers, strictly one-directional (`main → {business_rules, storage} → models`):

- `app/models.py` — Pydantic v2 data contract (enums + input/output models). **The
  source of truth.** Changing it ripples everywhere.
- `app/storage.py` — in-memory dict store; validates-before-commit; `_reset()` for tests.
- `app/business_rules.py` — pure functions: `validate_status_transition`, `is_overdue`.
- `app/main.py` — FastAPI routes, CORS, HTTP status mapping.
- `frontend/index.html` — single-file vanilla-JS Kanban (no build step).

Full diagram and data-flow: `docs/architecture.md`.

---

## 3. Backend responsibilities

- Own **all** validation and business rules — the UI only hints; the API enforces.
- Keep input models (`TaskCreate`/`TaskUpdate`) separate from output (`TaskResponse`),
  and keep `extra="forbid"` so clients can never set server-managed fields.
- Enforce the status lifecycle: `ToDo→InProgress`, `InProgress→Done`, `Done→InProgress`.
  Everything else (skips, reverts, same-to-same) is rejected with 422.
- Compute `overdue`; **never store it.**
- Preserve error-ordering guarantees: existence (404) before transition validity (422);
  surface storage `ValidationError` as 422, never an unhandled 500.
- Keep the store uncorruptible: validate the merged record before writing it back.

---

## 4. Frontend responsibilities

- Render three Kanban columns, sort cards High → Medium → Low.
- Call `GET /tasks` with query params (never filter locally-only); debounce search.
- Optimistic drag-and-drop with **rollback** on a rejected transition, showing the
  server message.
- Diff-based PATCH from the edit modal (send only changed fields) to avoid same-status
  422s.
- Maintain distinct loading / empty / ready / error states.
- **Escape every user-supplied field** with `escapeHtml()` before inserting into the
  DOM. Any new card field MUST also be escaped — this is a security invariant.

---

## 5. Testing strategy

- Tests exercise behavior through the API with FastAPI `TestClient`; the autouse
  `reset_storage` fixture keeps them deterministic.
- Run before and after any change:
  ```bash
  pytest tests/ -v          # full suite (currently 37 passing)
  python -m tests.verify_a  # 8 model checks
  ```
- **Never** weaken a test to make it pass. If a change breaks a test, either the change
  is wrong or the requirement changed (confirm with the human).
- Use the **Break Test**: after touching a rule, deliberately break it and confirm the
  right test fails, then restore. Details and recommended new unit tests:
  `docs/testing_strategy.md`.

---

## 6. Coding standards

- **Python:** Pydantic **v2 only** (`ConfigDict`, `@field_validator`) — no v1 patterns
  (`class Config`, `.dict()`). Type-hint everything. Timezone-aware UTC timestamps.
  Keep functions small and pure where possible. Match the existing high docstring
  density — explain *why*, not just *what*.
- **Layering:** never import "up" the stack (models must not import storage/main).
- **HTTP:** correct status codes are part of the contract (201 create, 204 delete-empty,
  404 missing, 422 validation). Do not change them casually.
- **Frontend:** vanilla JS, no dependencies, no build step. Keep the single-file
  structure unless asked to split it.
- **Style:** follow the surrounding code's conventions and naming exactly.

---

## 7. AI usage guidelines

- **Draft, then verify.** Treat AI output as a draft: read it before running it, run the
  suite, and break-test critical rules. A passing suite is not proof (a test can collude
  with a wrong implementation — this actually happened; see `docs/ai_usage_report.md`).
- **Respect scope.** Reject suggestions that add endpoints, fields, dependencies, or
  frameworks beyond the request. Historic rejected suggestions: a `/search` endpoint,
  client-side-only filtering, assignee search, a database migration.
- **Verify doc claims against code.** Never assert in documentation something you have
  not confirmed in the source and (for behavior) the test suite.
- **No secrets, ever**, in source. Keep the dependency set minimal.
- Governance record and validation process: `docs/ai_usage_report.md`.

---

## 8. Safe modification guidelines

**Safe (encouraged):** adding tests, adding/expanding docs, CI, Docker, `.gitignore`/
`.env.example` hygiene, dependency pinning notes, non-behavioral refactors that keep the
suite green.

**Requires explicit human confirmation:** changing status codes, transition rules, the
overdue definition, the data model, or CORS policy; adding a runtime dependency; adding
a product feature; changing persistence.

**Do NOT do without being asked:** rewrite git history, flatten the directory layout,
change business requirements, add authentication/persistence/frameworks, or "improve"
behavior that has passing tests.

**Always:** run `pytest tests/ -v` before and after; keep changes minimal and scoped;
update the relevant `docs/*` if behavior or setup changes.

---

## 9. Common workflows for future maintainers

**Add a backend test (safe):**
1. Add cases to `tests/test_tasks.py` / `test_midcourse.py`, or new
   `tests/test_business_rules.py` / `test_storage.py` (templates in
   `docs/testing_strategy.md`).
2. `pytest tests/ -v` → green.

**Fix a bug (no new feature):**
1. Write a failing test that reproduces it.
2. Fix the minimal code in the correct layer.
3. `pytest tests/ -v` → green; break-test the fix; update docs if the contract clarified.

**Run locally:**
```bash
python -m venv venv && source venv/bin/activate   # (Windows: venv\Scripts\activate)
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
python -m http.server 5500   # then open frontend/index.html
```

**Run in Docker / CI:** see `docs/deployment_guide.md` (Docker) and
`.github/workflows/ci.yml` (CI).

**Before committing:** suite green, docs updated, no secrets, scope respected. Prefer a
new commit over amending; branch off before committing to a shared branch.
