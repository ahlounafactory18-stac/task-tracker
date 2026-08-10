# Code Review

**Scope:** full review of the backend (`app/`), test suite (`tests/`), and frontend
(`frontend/index.html`) as of branch `mid-course-project`.
**Reviewer role:** Senior Software Engineer / Code Reviewer.
**Overall verdict:** **Approved for course submission.** The code is clean, well
layered, and well tested for its stated scope. Findings below are hardening and
maintainability suggestions, not release blockers. No product-feature changes are
recommended (out of scope).

---

## Strengths

1. **Clean, one-directional layering.** `main → {business_rules, storage} → models`.
   No circular imports, no leakage of HTTP concerns into the domain layer.
2. **Strict data contract.** Separate input (`TaskCreate`/`TaskUpdate`) and output
   (`TaskResponse`) models, enums instead of free strings, `extra="forbid"` blocks
   unknown and server-managed fields. This is the single most valuable design choice
   in the codebase.
3. **Validate-before-commit storage.** `update_task` builds a temporary merged copy,
   validates it by constructing a `TaskResponse`, and only then writes back. The store
   can never be corrupted by a rejected update — and there is a regression test for it.
4. **Business rules on the server.** Status transitions and overdue logic are enforced
   in the backend, not just hidden in the UI. A direct API caller cannot bypass them.
5. **Derived data is computed, not stored** (`is_overdue`), avoiding stale flags.
6. **Correct, deliberate error ordering.** Existence (404) is checked before transition
   validity (422); the ordering is documented *and* tested.
7. **Excellent docstrings.** Every module and function explains intent and the "why,"
   not just the "what." This is unusually good for a learning project.
8. **Deterministic, isolated tests.** Autouse store reset; overdue tests anchored to
   `today`; assertions check the specific returned item, not just "something."
9. **Dependency-free frontend** with real UX states (loading/empty/ready/error),
   optimistic drag with rollback, and diff-based PATCH to avoid same-status 422s.

---

## Weaknesses / issues

Ordered by impact. None block submission.

| # | Severity | Location | Issue |
|---|----------|----------|-------|
| W1 | Low | `app/storage.py` | Module-level mutable globals (`_tasks`, `_next_id`) make the store a singleton. Fine for this scope, but it prevents running two isolated app instances in one process and couples tests to `_reset()`. |
| W2 | Low | `frontend/index.html` | `BASE_URL` is hardcoded to `http://localhost:8000`. Any change of host/port requires editing source. Acceptable for local scope; a small config constant at top-of-file (already present) is the mitigation. |
| W3 | Low | `app/storage.py` | Not thread-safe. Uvicorn with `--workers 1` (default `--reload`) is single-process, so this is safe today, but concurrent writes under multiple workers could race. Documented as a scope limit. |
| W4 | Low | `app/main.py` | `list_tasks` applies filters as sequential list comprehensions (O(n) per filter). Perfectly fine for an in-memory learning store; would need indexing/pagination at scale. |
| W5 | Info | `requirements.txt` | Dependencies are lower-bound (`>=`) with no lockfile, so builds are not perfectly reproducible. See `docs/dependency_review.md`. |
| W6 | Info | Tests | Business rules and storage are only tested through the API, not as isolated units. See `docs/testing_strategy.md` for recommended unit tests. |
| W7 | Info | Repo layout | The project is nested one level deep (`task-tracker/task-tracker/`). The inner directory is the real root and git repo. Harmless but can confuse tooling/CI paths. |

---

## Technical debt

- **In-memory persistence.** By design for Modules 1–3, but it is the single largest
  gap between this project and a production service. Any future persistence work
  should be introduced *behind the existing `storage.py` interface* so `main.py` and
  the tests barely change.
- **No coverage measurement.** Coverage is implied by inspection, not measured. Adding
  `pytest-cov` in CI would make regressions in coverage visible.
- **Frontend is untested by automation.** The JS logic (query building, optimistic
  rollback, modal validation) is verified manually. A future improvement would extract
  the pure helpers and test them, but that is out of the current Module scope.

---

## Maintainability concerns

- **Singleton store + `_reset()` coupling (W1/W3).** The cleanest future refactor is to
  wrap state in a small `Storage` class instantiated once and injected via FastAPI
  dependencies. This removes globals, enables per-test instances without `_reset()`,
  and makes concurrency handling localizable. *Not required now.*
- **Single-file frontend.** ~700 lines of HTML+CSS+JS in one file is readable today but
  will not scale. If the UI grows, split CSS/JS into separate files or adopt a small
  framework — a larger decision than this project needs.
- **Config sprawl risk.** `BASE_URL` (frontend) and the CORS regex (backend) both encode
  "localhost" assumptions in two places. If the app is ever deployed, both must change
  together; document that link (done in `docs/security_review.md` and the deployment guide).

---

## Refactoring recommendations (optional, non-breaking)

Prioritized; all are safe, none change behavior or add features.

1. **Add unit tests** for `business_rules` and `storage` (see testing strategy). Highest
   value-to-effort ratio.
2. **Add `pytest-cov`** and enforce a coverage floor in CI.
3. **(Future) Extract a `Storage` class** behind the current function API so persistence
   can be swapped in later without touching routes or tests.
4. **(Future) Make `BASE_URL` configurable** in the frontend (e.g. read from a
   `window.__CONFIG__` set by the host page) if the app is ever served from a non-local
   origin.
5. **Flatten the nested directory** (`task-tracker/task-tracker/` → single root) in a
   dedicated commit if the assessors run tooling from the outer folder. Left as-is here
   to avoid rewriting git history mid-submission.

---

## File-by-file notes

- **`app/models.py`** — Exemplary. Clear enums, a shared `_clean_title` helper reused by
  both input models, explicit `MAX_TITLE_LENGTH` constant. No changes recommended.
- **`app/storage.py`** — Correct and well-documented. Only debt is the singleton pattern
  (W1/W3), acceptable for scope.
- **`app/business_rules.py`** — Pure, injectable, easy to test. `VALID_TRANSITIONS` as a
  `frozenset` of pairs is the right model. No changes recommended.
- **`app/main.py`** — Thin and correct. Good handling of the storage-`ValidationError` →
  `RequestValidationError` mapping. No changes recommended.
- **`tests/`** — Strong behavioral coverage; add unit tests as noted.
- **`frontend/index.html`** — Solid UX and correct API usage; main note is the hardcoded
  `BASE_URL` and lack of automated tests.

## Conclusion

The codebase is clean, cohesive, and correct for its scope, with a data contract and a
validate-before-commit store that are notably better than typical for a learning
project. The recommended work is additive (unit tests, coverage, CI, Docker) and
introduces no product features. **Approved.**
