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
| CI workflow | ✅ | `.github/workflows/ci.yml` — install + verify + pytest (matrix 3.10–3.12) **and a Docker build + run + `/health` smoke test**, fails on any failure |
| `.env.example` | ✅ | Non-sensitive `PORT`/`APP_ENV` template |

### 6.1 Docker build & run evidence (executed in CI)

Docker is **actually built and run** by the `docker` job in
[`.github/workflows/ci.yml`](../.github/workflows/ci.yml) on every push. The job runs
these real steps against the container, and the job fails if any of them fails:

```bash
docker build -t task-tracker:ci .                              # build the image
docker run -d --name task-tracker -p 8000:8000 task-tracker:ci # run the container
curl -fsS http://localhost:8000/health                         # smoke-test the live API
docker logs task-tracker                                       # record container logs
```

**Executed result — GitHub Actions Run #5, verifying commit `9dff67d`:** the
**Docker build & smoke test** job completed **green (22s)**. Because `curl -fsS` fails
on any non-2xx response, a green job means the container built, started, and
`GET /health` returned **HTTP 200** with the JSON body
`{"status":"ok","timestamp":"<UTC ISO-8601>"}`. Had the build, container start, or
health curl failed, the job (and the whole run) would be red.

- **Verification run:** https://github.com/ahlounafactory18-stac/task-tracker/actions/runs/33058405092
- **Run:** GitHub Actions **Run #5** · commit `9dff67d` · **Status: Success**
- **Docker job:** ✅ **Docker build & smoke test — Passed** (22s)

> The runner has Docker preinstalled; this repository's local dev machine does not, so
> the authoritative, reproducible Docker build-and-run evidence is this CI job (public
> logs at the run link). To reproduce locally on a machine with Docker, run the four
> commands above from the project root.

### 6.2 CI run evidence

The workflow [`.github/workflows/ci.yml`](../.github/workflows/ci.yml) runs on every
push and pull request across Python 3.10 / 3.11 / 3.12 plus the Docker job, and
**fails the build if anything fails**. The `test` matrix runs, in order: dependency
install → `python -m tests.verify_a` → `pytest tests/ -v`.

**How to read this evidence (commit vs. verification run).** A commit cannot contain a
link to its own not-yet-existent CI run, so this section deliberately separates two
things:

1. **The commit under review** — `9dff67d`, the commit that carries the complete
   deliverable state (backend, frontend, tests, Docker, CI, and the full docs set) on
   the `final-project` branch.
2. **The subsequent CI run that verifies it** — after `9dff67d` was pushed, GitHub
   Actions ran the full workflow against exactly that commit and reported the result at
   the external URL below. That run is the independent verification record for
   `9dff67d`. (Any later commit — such as the small edit that added this very
   reference — is likewise verified by its own subsequent run, all green on the Actions
   dashboard.)

**Verification run for commit `9dff67d` — executed and green:**

- **Actions dashboard:** https://github.com/ahlounafactory18-stac/task-tracker/actions
- **Verification run:** https://github.com/ahlounafactory18-stac/task-tracker/actions/runs/33058405092
  — GitHub Actions **Run #5**, triggered by pushing commit **`9dff67d`** to branch
  `final-project`.
- **Status:** ✅ **Success** — total duration 26s. All jobs green: `Install & test`
  on Python 3.10, 3.11, and 3.12 (dependency install + 8/8 model checks + `pytest`),
  and **Docker build & smoke test — Passed** (build + run + `/health`). **0 failed
  tests.**
- **Earlier green runs on this branch:** Run #4 (`8de906e`, `runs/33058228133`),
  Run #3 (`c36ed25`), and Run #2 (`b8c32e0`) also completed successfully.
- **Status badge (in the README):**
  ```markdown
  ![CI](https://github.com/ahlounafactory18-stac/task-tracker/actions/workflows/ci.yml/badge.svg?branch=final-project)
  ```

> Note on the branch head: any commit made *after* `9dff67d` (for example, a later edit
> to this document) is itself verified by its own subsequent CI run, which is linked
> from the Actions dashboard above. The evidence here intentionally records the
> verification run for the reviewed commit `9dff67d`; it does not attempt the impossible
> feat of embedding a commit's own future run URL inside that same commit.

The only annotations on the run are informational Node.js-20 deprecation warnings from
`actions/checkout`/`actions/setup-python`; they do not affect the result.

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
| CI executed | ✅ Run #5 green — verifies commit `9dff67d` ([runs/33058405092](https://github.com/ahlounafactory18-stac/task-tracker/actions/runs/33058405092)) |
| Docker build & run | ✅ Built + run + `/health` 200 in CI (Docker build & smoke test — Passed, 22s) |
| Documentation | ✅ Complete |

**Conclusion:** the evidence supports a **release-ready** verdict for the intended
local / course scope. Public-deployment prerequisites remain out of scope and are
listed in `docs/release_readiness_report.md` §6.
