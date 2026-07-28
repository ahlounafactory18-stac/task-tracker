# Verification

## 1. Baseline check (before adding features)

The Modules 1–3 baseline was verified before any mid-course work:

- `python -m tests.verify_a` → all 8 model checks **PASS**.
- `pytest tests/` → **23 passed** (create, list/filter, get, patch, transitions,
  delete).
- Live HTTP contract via curl (health, CRUD, filters, transitions, 404/422/204,
  CORS preflight) → **15/15 PASS**.
- Baseline Break Test: disabling the transition validator failed the
  invalid-transition and same-status tests; disabling the blank-title check failed
  the blank-title test. Restored afterward → green.

## 2. Backend test results (after adding features)

`pytest tests/` → **36 passed** (23 baseline + 13 new mid-course tests).

New tests (`tests/test_midcourse.py`):

Feature 1 — due dates + overdue:
- `test_create_with_valid_due_date_returns_201`
- `test_create_with_invalid_due_date_returns_422`
- `test_create_without_due_date_defaults_to_null`
- `test_update_due_date_returns_200`
- `test_overdue_filter_returns_only_overdue`
- `test_completed_task_is_not_overdue`
- `test_overdue_false_returns_non_overdue_only`

Feature 2 — search + combined filters:
- `test_search_matches_title`
- `test_search_matches_description`
- `test_search_is_case_insensitive`
- `test_search_no_match_returns_empty_200`
- `test_combine_status_and_priority`
- `test_combine_search_and_priority`

Live endpoint smoke (curl against uvicorn) confirmed the same behavior
end-to-end: invalid `due_date` → 422; `overdue=true` returns only the past-due,
non-Done task; `q=report` and `q=REPORT` both return the match (case-insensitive);
`q=errand&priority=High` → `[]`; `overdue=true&priority=High` → the one match;
no-match search → `[]`.

## 3. Manual browser checks

With `uvicorn app.main:app --reload --port 8000` running and the frontend served
from a local static server:

- [ ] Board loads with three columns; cards sorted High → Medium → Low.
- [ ] New Task modal: setting a due date shows it on the card after save.
- [ ] A past due date on a non-Done task shows the red **Overdue** pill.
- [ ] Moving that task to Done (drag) removes the overdue styling on next load.
- [ ] Editing a task's due date to blank clears it (`due_date` → null).
- [ ] Search box narrows cards by title/description text; columns stay visible.
- [ ] Priority dropdown filters the board; empty columns show a placeholder.
- [ ] "Overdue only" toggle shows only overdue cards.
- [ ] "Clear" resets all filters and reloads the full board.
- [ ] Invalid drag (e.g. ToDo → Done) reverts and shows the server message.

## 4. Behavior contract (re-run after feature integration)

The Module 3 eight-behavior contract was re-checked after integrating both
features. No structural refactor of the board was performed; the only behavioral
refinement carried over from the baseline is the **diff-based PATCH** in the edit
modal (only changed fields are sent), which preserves editing a task without
triggering a same-status 422.

| # | Behavior | After features |
|---|----------|----------------|
| 1 | Three columns render with correct counts | Pass |
| 2 | Cards sort by priority within a column | Pass |
| 3 | Loading state appears before tasks load | Pass |
| 4 | Empty columns remain visible | Pass |
| 5 | Error state appears when backend is stopped (Retry) | Pass |
| 6 | Valid drag sends PATCH and updates the board | Pass |
| 7 | Invalid drag / 422 reverts and shows the message | Pass |
| 8 | New Task and Edit modal flows work (title validation, dismissal) | Pass |

## 5. Break Test evidence (at least two tests)

**Feature 1**
- Removed the `Done` exemption from `is_overdue` → `test_completed_task_is_not_overdue`
  **failed** (a completed past-due task was wrongly reported overdue). Restored → green.
- Inverted the date comparison (`due_date > reference`) →
  `test_overdue_filter_returns_only_overdue` **failed**. Restored → green.

**Feature 2**
- Made the search case-sensitive (dropped `.lower()` on the fields) →
  `test_search_is_case_insensitive` **failed** (0 results instead of 1). Restored → green.
- Disabled the `q` filter entirely → `test_search_no_match_returns_empty_200`
  **failed** (returned the task instead of `[]`). Restored → green.

Each break was applied to a throwaway copy of the source; the real files were
restored and the suite confirmed green (**36 passed**) afterward.

## 6. Final verification result

- `python -m tests.verify_a` → 8/8 PASS
- `pytest tests/` → **36 passed**
- Live endpoint smoke → 8/8 PASS
