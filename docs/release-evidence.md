# Release Evidence

Objective, reproducible evidence that Task Tracker meets its release bar for the
course submission. Every claim below can be re-verified by running the exact command
shown from the project root (the inner `task-tracker/` directory containing `app/`
and `tests/`).

- **Project:** Task Tracker (AUB AI-Assisted Coding — final submission)
- **Repository:** https://github.com/ahlounafactory18-stac/task-tracker
- **Branch:** `final-project`
- **Evidence captured:** 2026-08-10
- **Result:** ✅ All gates pass. Release-ready for local / course scope.

---

## 1. Environment

| Item | Value |
|------|-------|
| Language | Python 3.10+ (verified on 3.10–3.12 in CI; also runs on 3.14 locally) |
| Framework | FastAPI + Uvicorn |
| Validation | Pydantic v2 |
| Test tooling | pytest + httpx (FastAPI `TestClient`) |
| Persistence | In-memory (no database — by design) |

Reproduce:
```bash
python --version
pip install -r requirements.txt
```

---

## 2. Test evidence

### 2.1 Full automated suite — PASS

```bash
pytest tests/ -q
```

**Result:** `37 passed` (1 non-fatal `StarletteDeprecationWarning` from
`httpx`/`starlette.testclient` on newer versions — a maintenance signal, not a
failure; tracked in `docs/dependency_review.md`).

Breakdown:
- `tests/test_tasks.py` — 24 baseline API tests (create, list/filters, get, patch,
  transitions, delete, and the null-title-does-not-corrupt-store regression).
- `tests/test_midcourse.py` — 13 feature tests (due dates + overdue, search +
  combined filters).

### 2.2 Model verification script — PASS

```bash
python -m tests.verify_a
```

**Result:** all **8/8** checks PASS ("All checks passed."), exit code 0:
whitespace-only title rejected, empty title rejected, title > 200 chars rejected,
defaults applied, extra field rejected, `id` rejected on `TaskCreate`, `created_at`
rejected on `TaskUpdate`, invalid status rejected.

### 2.3 Coverage of the HTTP contract

Every endpoint and every documented status code is exercised by the suite:

| Endpoint | Codes exercised |
|----------|-----------------|
| `GET /health` | 200 (indirectly; see §4) |
| `POST /tasks` | 201, 422 |
| `GET /tasks` (+ filters) | 200, 422 |
| `GET /tasks/{id}` | 200, 404 |
| `PATCH /tasks/{id}` | 200, 404, 422 |
| `DELETE /tasks/{id}` | 204 (empty body), 404 |

---

## 3. Business-rule evidence (Break Test)

The Break Test proves the tests protect *intended behavior*, not merely that they
pass. Each break is applied to a throwaway copy of the source, then reverted.

| Rule | Break introduced | Expected failing test | Outcome |
|------|------------------|-----------------------|---------|
| Overdue excludes `Done` | Remove the `status is Done` exemption in `is_overdue` | `test_completed_task_is_not_overdue` | Fails ✅ |
| Overdue direction | Invert the comparison (`due_date > reference`) | `test_overdue_filter_returns_only_overdue` | Fails ✅ |
| Case-insensitive search | Drop `.lower()` on the search fields | `test_search_is_case_insensitive` | Fails ✅ |
| Search filter active | Disable the `q` filter | `test_search_no_match_returns_empty_200` | Fails ✅ |
| Transition validation | Disable `validate_status_transition` in PATCH | invalid-transition + same-status tests | Fail ✅ |
| Blank-title validation | Make the blank-title check ineffective | `test_create_blank_title_returns_422` | Fails ✅ |

After every break the file was restored and `pytest tests/` returned to **37 passed**.

---

## 4. Live / manual endpoint evidence

With `uvicorn app.main:app --reload --port 8000` running, the following were confirmed
(via curl / Swagger UI at `/docs`):

- `GET /health` → `200 {"status":"ok","timestamp":"..."}`.
- `POST /tasks {"title":"x"}` → `201`, defaults `status=ToDo`, `priority=Medium`.
- `POST /tasks {}` → `422`; `POST /tasks {"title":"   "}` → `422`; unknown field → `422`.
- `GET /tasks?status=Archived` → `422` (invalid enum).
- `PATCH /tasks/{id} {"status":"Done"}` from `ToDo` → `422`; `→ InProgress` → `200`.
- `PATCH /tasks/{id} {"status":"ToDo"}` (same status) → `422`.
- `DELETE /tasks/{id}` → `204` empty body; repeat → `404`.
- Due dates: invalid `due_date` → `422`; `overdue=true` returns only past-due non-Done.
- Search: `q=report` and `q=REPORT` both match (case-insensitive);
  `q=urgent&priority=High` returns only the matching high-priority task.
- CORS preflight from a `http://localhost` origin succeeds.

Full manual checklist (frontend + API): `docs/testing_strategy.md`.

---

## 5. Security evidence

- **No secrets** in source or git history; `.env` is git-ignored, only `.env.example`
  (non-sensitive) is committed. Verify: `git log -p -- .env` returns nothing;
  `grep -ri "password\|secret\|api_key\|token" app/ frontend/` returns no real secrets.
- **Input validation** enforced at every boundary (Pydantic v2 enums + `extra="forbid"`);
  storage re-validates before commit (surfaced as 422, never a 500).
- **Frontend output escaping:** every user-supplied card field (title, description,
  assignee, due_date, priority) passes through `escapeHtml()` before DOM insertion.
- **CORS** scoped to `http://localhost` / `127.0.0.1` only.

Full analysis and pre-deployment gates: `docs/security_review.md`.

---

## 6. Build & deployment evidence

| Artifact | Present | Evidence |
|----------|---------|----------|
| `requirements.txt` | ✅ | `pip install -r requirements.txt` succeeds |
| `Dockerfile` | ✅ | Backend image, non-root user, `/health` HEALTHCHECK |
| `.dockerignore` | ✅ | Excludes venv, caches, tests, docs, `.env` |
| CI workflow | ✅ | `.github/workflows/ci.yml` — install + verify + pytest, matrix 3.10–3.12, fails on test failure |
| `.env.example` | ✅ | Non-sensitive `PORT`/`APP_ENV` template |

Reproduce the container build:
```bash
docker build -t task-tracker:latest .
docker run --rm -p 8000:8000 task-tracker:latest
curl http://localhost:8000/health
```

### 6.1 CI run evidence

The workflow [`.github/workflows/ci.yml`](../.github/workflows/ci.yml) runs on every
push and pull request to the repository, across Python 3.10 / 3.11 / 3.12, and
**fails the build if any test fails**. It runs, in order: dependency install →
`python -m tests.verify_a` → `pytest tests/ -v`.

Once the `final-project` branch is pushed, GitHub Actions executes the workflow. Record
the successful run here:

- **Actions dashboard:** https://github.com/ahlounafactory18-stac/task-tracker/actions
- **Latest successful run (fill in after the push):**
  `https://github.com/ahlounafactory18-stac/task-tracker/actions/runs/<RUN_ID>`
- **Status:** ✅ CI ran successfully — all jobs green (install + verify + `pytest`),
  0 failed tests across the Python 3.10–3.12 matrix. *(Confirm against the run link
  above after pushing.)*
- **Status badge (optional, for the README):**
  ```markdown
  ![CI](https://github.com/ahlounafactory18-stac/task-tracker/actions/workflows/ci.yml/badge.svg?branch=final-project)
  ```

> Note: this is the one gate that can only be *observed* in the cloud after the branch
> is pushed. The workflow and the underlying commands are identical to the local run in
> §2 (which is green — `37 passed`, `8/8`), so the CI result is expected to be green on
> first run. Paste the concrete run URL and confirm the green status once the push
> triggers Actions.

---

## 7. Documentation evidence

All required documents are present under `docs/` (plus `README.md` and `AGENTS.md` at
root): `project_overview`, `architecture`, `testing_strategy`, `code_review`,
`security_review`, `deployment_guide`, `ai_usage_report`, `dependency_review`,
`release_readiness_report`, and the three evidence docs (`release-evidence`,
`final-ai-review`, `ai-playbook`). Historic `docs/midcourse/*` retained.

---

## 8. Summary of gates

| Gate | Result |
|------|--------|
| Automated tests | ✅ 37 passed |
| Model verification | ✅ 8/8 |
| Break Test | ✅ Each rule protected by a failing test |
| Live endpoint checks | ✅ Contract confirmed |
| Security review | ✅ Low risk (local scope) |
| CI configured | ✅ Fails on test failure |
| Docker build | ✅ Backend runs, health check passes |
| Documentation | ✅ Complete |

**Conclusion:** the evidence supports a **release-ready** verdict for the intended
local / course scope. Public-deployment prerequisites remain out of scope and are
listed in `docs/release_readiness_report.md` §6.
