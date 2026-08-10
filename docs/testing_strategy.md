# Testing Strategy

## Philosophy

The backend is the trusted boundary, so it is where the tests live. Every business
rule and every error contract (status codes) is verified through the public HTTP
surface using FastAPI's `TestClient`. The suite is deterministic: an autouse fixture
resets the in-memory store before and after every test, so no test can leak state
into another.

A green suite is treated as necessary but not sufficient. The project also uses a
**Break Test** discipline (see below): deliberately breaking production code to
confirm the *right* test fails proves the tests actually protect behavior, not just
that they pass.

## How to run the tests

```bash
# full API suite (verbose)
pytest tests/ -v

# quiet summary
pytest tests/ -q

# model verification script (8 standalone checks, exits non-zero on failure)
python -m tests.verify_a
```

Current status: **37 passed** (`test_tasks.py` + `test_midcourse.py`), plus 8 checks
in `verify_a.py`.

## Test inventory

### `tests/conftest.py` — shared fixtures
- `reset_storage` (autouse) — clears the store before and after each test.
- `client` — a FastAPI `TestClient`.
- `created_task` — creates one default task and returns its JSON.

### `tests/test_tasks.py` — baseline API (24 tests)
- **Create:** 201 happy path, missing title → 422, blank title → 422, defaults
  applied, extra field rejected.
- **List + filters:** empty list → 200 `[]`, list all, filter by priority, no-match
  → 200 `[]`, invalid filter value → 422.
- **Get by id:** existing → 200, missing → 404.
- **Patch:** field update → 200, missing → 404, invalid payload → 422,
  existence-checked-before-transition (404 not 422).
- **Status transitions:** valid `ToDo→InProgress`, invalid `ToDo→Done` → 422,
  same-status no-op → 422, reopen `Done→InProgress`, title-only edit skips the
  transition check, and the regression test that a rejected null-title update does
  **not** corrupt the store.
- **Delete:** existing → 204 with empty body, missing → 404.

### `tests/test_midcourse.py` — mid-course features (13 tests)
- **Due dates + overdue:** valid due date → 201, invalid date → 422, default null,
  update due date → 200, overdue filter returns only overdue, completed task is not
  overdue, `overdue=false` returns only non-overdue.
- **Search + combined filters:** match title, match description, case-insensitive,
  no-match → 200 `[]`, combine status + priority, combine search + priority.

### `tests/verify_a.py` — model verification script (8 checks)
Standalone gate covering: whitespace-only title rejected, empty title rejected,
title > 200 chars rejected, defaults applied, extra field rejected, `id` rejected on
`TaskCreate`, `created_at` rejected on `TaskUpdate`, invalid status rejected.

## Existing coverage — strengths

- Every endpoint and every documented status code (200/201/204/404/422) is exercised.
- Business rules are covered through the API: transition validity, overdue logic
  (including the `Done` exemption), search semantics, and AND-combined filters.
- A real regression is locked in: the null-title-does-not-corrupt-store test.
- Deterministic dates (relative to `today`) keep the overdue tests correct over time.

## Coverage gaps

These are gaps, not defects — the behavior is exercised indirectly. Adding them
would raise confidence and unit-level isolation.

| Gap | Why it matters | Priority |
|-----|----------------|----------|
| No direct unit tests for `business_rules.is_overdue` / `validate_status_transition` | Currently only tested via the API; a pure-function unit test pins edge cases (due today, `today` injection) precisely | Medium |
| No direct unit tests for `storage` (`add_task`, `update_task` rollback, `_reset`) | The validate-before-commit guarantee is only tested through PATCH | Medium |
| No test for `GET /health` | Simple but part of the contract (used by Docker/CI health checks) | Low |
| No CORS behavior test | The localhost-regex policy is untested | Low |
| No coverage measurement | `pytest-cov` would quantify and guard coverage in CI | Low |
| No frontend tests | `index.html` logic (query building, optimistic rollback) is verified manually only | Low (out of Module scope) |

## Recommended additional tests

Add a `tests/test_business_rules.py` and `tests/test_storage.py` for unit-level
isolation. Suggested cases:

```python
# tests/test_business_rules.py
from datetime import date
from app.business_rules import is_overdue, validate_status_transition
from app.models import TaskStatus

def test_due_today_is_not_overdue():
    assert is_overdue(date(2026, 1, 10), TaskStatus.ToDo, today=date(2026, 1, 10)) is False

def test_past_due_todo_is_overdue():
    assert is_overdue(date(2026, 1, 9), TaskStatus.ToDo, today=date(2026, 1, 10)) is True

def test_done_is_never_overdue():
    assert is_overdue(date(2026, 1, 1), TaskStatus.Done, today=date(2026, 1, 10)) is False

def test_no_due_date_is_not_overdue():
    assert is_overdue(None, TaskStatus.ToDo, today=date(2026, 1, 10)) is False

def test_same_status_transition_rejected():
    assert validate_status_transition(TaskStatus.ToDo, TaskStatus.ToDo) is False

def test_skip_transition_rejected():
    assert validate_status_transition(TaskStatus.ToDo, TaskStatus.Done) is False
```

```python
# tests/test_storage.py
import pytest
from app import storage
from app.models import TaskCreate

@pytest.fixture(autouse=True)
def _reset():
    storage._reset(); yield; storage._reset()

def test_ids_start_at_one_and_increment():
    a = storage.add_task(TaskCreate(title="a"))
    b = storage.add_task(TaskCreate(title="b"))
    assert (a.id, b.id) == (1, 2)

def test_update_missing_returns_none():
    assert storage.update_task(999, {"title": "x"}) is None

def test_rejected_update_leaves_store_unchanged():
    t = storage.add_task(TaskCreate(title="keep"))
    with pytest.raises(Exception):
        storage.update_task(t.id, {"title": None})
    assert storage.get_task_by_id(t.id).title == "keep"
```

Also recommended: add `pytest-cov` and run `pytest --cov=app --cov-report=term-missing`
in CI, targeting ≥ 90 % line coverage on `app/`.

## Manual verification checklist

Run the backend (`uvicorn app.main:app --reload --port 8000`) and serve the frontend
from a local static server, then confirm:

**API (curl or Swagger UI at `/docs`)**
- [ ] `GET /health` returns `{"status":"ok","timestamp":...}`.
- [ ] `POST /tasks` with `{"title":"x"}` → 201 with id, defaults (`ToDo`/`Medium`).
- [ ] `POST /tasks` with `{}` → 422; with `{"title":"  "}` → 422.
- [ ] `POST /tasks` with an unknown field → 422.
- [ ] `GET /tasks` → 200 list; invalid `status` filter → 422.
- [ ] `GET /tasks/999` → 404.
- [ ] `PATCH /tasks/{id}` `ToDo→Done` → 422; `ToDo→InProgress` → 200.
- [ ] `PATCH /tasks/{id}` `ToDo→ToDo` (same status) → 422.
- [ ] `DELETE /tasks/{id}` → 204 empty body; deleting again → 404.

**Frontend (browser)**
- [ ] Board loads with three columns; cards sorted High → Medium → Low.
- [ ] New Task modal: setting a due date shows it on the card after save.
- [ ] A past due date on a non-Done task shows the red **Overdue** pill.
- [ ] Dragging that task to Done removes the overdue styling on next load.
- [ ] Editing a due date to blank clears it (`due_date → null`).
- [ ] Search narrows cards by title/description; columns stay visible.
- [ ] Priority dropdown filters; empty columns show a placeholder.
- [ ] "Overdue only" toggle shows only overdue cards.
- [ ] "Clear" resets all filters and reloads the full board.
- [ ] An invalid drag (`ToDo→Done`) reverts and shows the server message.
- [ ] Stopping the backend shows the error state with a working Retry.

## Break Test discipline

For each critical rule, break the source, run pytest, confirm the *specific*
protecting test fails, then restore. Proven examples from `docs/midcourse/verification.md`:

- Remove the `Done` exemption in `is_overdue` → `test_completed_task_is_not_overdue`
  fails.
- Invert the date comparison → `test_overdue_filter_returns_only_overdue` fails.
- Drop `.lower()` in search → `test_search_is_case_insensitive` fails.
- Disable transition validation in PATCH → the invalid-transition and same-status
  tests fail.

Always apply breaks to a throwaway copy, then restore and confirm the suite is green.
