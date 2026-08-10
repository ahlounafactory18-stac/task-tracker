# Release Readiness Report

**Project:** Task Tracker (AUB AI-Assisted Coding — final course submission)
**Branch:** `mid-course-project`
**Date of assessment:** 2026-08-10
**Assessed by:** Senior Software / QA / DevOps review
**Overall recommendation:** ✅ **Release-ready for its stated scope** (local,
single-user learning project / course submission). **Not** approved for public
internet deployment without the changes listed in §6 and `docs/security_review.md`.

---

## 1. Project summary

Task Tracker is a two-tier task-management app: a FastAPI backend with an in-memory
store and a single-file vanilla-JS Kanban frontend. It supports full CRUD, a controlled
status lifecycle enforced on the server, optional due dates with a server-computed
overdue indicator, and case-insensitive search combinable (AND) with status/priority/
overdue filters. Scope is deliberately limited to the course's Modules 1–3 plus two
mid-course features. See `docs/project_overview.md` and `docs/architecture.md`.

---

## 2. Testing status ✅

| Item | Status |
|------|--------|
| Automated test suite | **37 passed** (`pytest tests/`) |
| Model verification script | **8/8 PASS** (`python -m tests.verify_a`) |
| Endpoint/status-code coverage | All endpoints and codes (200/201/204/404/422) exercised |
| Business-rule coverage | Transitions, overdue logic, search, combined filters |
| Regression coverage | Null-title-does-not-corrupt-store locked in |
| Break Test discipline | Applied and documented |
| Known gaps | No isolated unit tests for `business_rules`/`storage`; no coverage metric; no automated frontend tests |

Testing is **strong for the scope**. Recommended additions (unit tests, `pytest-cov`)
are documented in `docs/testing_strategy.md` and are enhancements, not blockers.

---

## 3. Documentation status ✅

| Document | Present |
|----------|---------|
| `README.md` (full) | ✅ |
| `AGENTS.md` | ✅ |
| `docs/project_overview.md` | ✅ |
| `docs/architecture.md` | ✅ |
| `docs/testing_strategy.md` | ✅ |
| `docs/code_review.md` | ✅ |
| `docs/security_review.md` | ✅ |
| `docs/deployment_guide.md` | ✅ |
| `docs/ai_usage_report.md` | ✅ |
| `docs/dependency_review.md` | ✅ |
| `docs/release_readiness_report.md` | ✅ (this file) |
| `docs/midcourse/*` (history) | ✅ (pre-existing) |

Documentation is **complete** for submission.

---

## 4. Security status ⚠️ (Low risk for local scope)

- ✅ No secrets in source or history; `.env` git-ignored.
- ✅ Strong input validation at every boundary (Pydantic v2, enums, `extra="forbid"`).
- ✅ Frontend escapes all user-supplied fields (`escapeHtml`).
- ⚠️ **No authentication** — acceptable only because the app is local.
- ⚠️ **Permissive-but-localhost CORS** — must be tightened before deployment.
- ⚠️ Dependencies use lower-bound pins with no lockfile.

Overall **low risk for the intended local scope**. Full analysis and the pre-deployment
gate in `docs/security_review.md`.

---

## 5. Deployment readiness ⚙️

| Capability | Status |
|-----------|--------|
| Local run (uvicorn) | ✅ Documented and working |
| Dockerfile + `.dockerignore` | ✅ Added; backend runs in a container with a `/health` check |
| CI (GitHub Actions) | ✅ Added; installs deps, runs verify script + full suite, fails on test failure, matrix Py 3.10–3.12 |
| `.env.example` | ✅ Present |
| Persistence | ❌ In-memory only (by design) — data lost on restart |
| Public deployment | ❌ Blocked until §6 items are done |

Ready to **run and demonstrate** locally and in Docker, and to be **verified in CI**.

---

## 6. Remaining risks

| # | Risk | Severity (local scope) | Mitigation / Owner action |
|---|------|------------------------|---------------------------|
| R1 | No persistence — data lost on restart | Accepted (by design) | Introduce a datastore behind `storage.py` before real use |
| R2 | No authentication on the API | Accepted (local only) | Add auth before any network exposure |
| R3 | CORS permits all localhost origins | Low | Replace with explicit allow-list before deployment |
| R4 | Lower-bound dependency pins, no lockfile | Low | Commit a lockfile; add `pip-audit`/Dependabot |
| R5 | No unit tests for pure logic; no coverage metric | Low | Add `test_business_rules.py`/`test_storage.py` + `pytest-cov` |
| R6 | Single-process, not thread-safe store | Accepted (local) | Localize concurrency handling if scaled |
| R7 | Nested `task-tracker/task-tracker/` layout | Cosmetic | Optionally flatten; ensure CI/Docker run from the inner root |
| R8 | `httpx`/`starlette` TestClient deprecation warning | Info | Track and migrate on next stack upgrade |

None of R1–R8 blocks the course submission; R1–R3 block public deployment.

---

## 7. Final release recommendation

**APPROVED for course submission and local/Docker demonstration.**

The project is clean, correctly layered, fully documented, and backed by a green,
meaningful test suite with CI and Docker in place. Its limitations (in-memory storage,
no auth) are intentional scope decisions, clearly documented, and appropriate for a
learning project.

**Conditional hold for any public deployment:** complete R2 (auth), R3 (CORS lock-down),
R1 (persistence), and R4 (dependency pinning) first, per `docs/security_review.md` and
`docs/deployment_guide.md`.

**Sign-off:** ready to submit to course assessors.
