# Prompt Log

A record of the meaningful prompts used to build each feature, what the AI
returned, and what was accepted, edited, or rejected. Prompts follow the Module
four-part shape: role/context, task, constraints, output format.

---

## Feature 1 — Due dates + overdue filter

### Prompt 1.1 — weak version, then rewritten (weak → strong)

**Weak prompt**
> Add due dates to my task tracker.

Why it is weak: no field name or type, no validation rule, no decision on where
"overdue" is computed, no scope guard against new dependencies.

**Rewritten (strong) prompt**
> You are working in a FastAPI + Pydantic v2 Task Tracker with an in-memory store.
> Task: add one optional field `due_date` (a date) to `TaskCreate`, `TaskUpdate`,
> and `TaskResponse`. Keep server-managed fields out of input models.
> Constraints: no new dependencies; rely on Pydantic to reject malformed dates with
> 422; do not store an "overdue" flag — it must be computed. Add a helper
> `is_overdue(due_date, status, today=None)` where overdue means due date strictly
> before today AND status is not Done. Output: the exact edits to `models.py`,
> `storage.py`, and `business_rules.py`.

**Result / decision:** Accepted the model and storage edits as-is. Accepted the
helper but **edited** it — the first draft omitted the `Done` exemption, which
would flag completed tasks as overdue. Added the `status is TaskStatus.Done` guard.

### Prompt 1.2 — overdue filter on the list endpoint

> Extend `GET /tasks` with an `overdue: bool | None` query parameter that combines
> with the existing status/priority filters. `overdue=true` returns only overdue
> tasks, `overdue=false` only non-overdue. Use `is_overdue`. Do not add a new route.

**Result / decision:** Accepted. Confirmed by a live curl check that `overdue=true`
returned exactly the past-due, non-Done task.

### Prompt 1.3 — tests for the feature

> Write pytest tests using the existing TestClient/fixtures for: valid due date
> (201), invalid date format (422), update due date (200), overdue filter returns
> only overdue, and a completed-task-is-not-overdue case. Build dates relative to
> today so the suite stays correct over time.

**Result / decision:** Accepted with a small **edit** — pinned the relative
`PAST`/`FUTURE` dates to module-level constants so every test uses the same anchor.

---

## Feature 2 — Search + combined filters

### Prompt 2.1 — backend search

> In the same `GET /tasks` endpoint, add a `q: str | None` parameter that does a
> case-insensitive substring match over title and description, combined (AND) with
> status, priority, and overdue. No new endpoint, no new dependency. A no-match
> result must be 200 with `[]`.

**Result / decision:** Accepted. **Rejected** a follow-up suggestion to also match
against the assignee field — assignee search was not in the story set, so it was
left out to keep scope tight.

### Prompt 2.2 — frontend filter bar

> Add a compact filter bar above the Kanban board with a search input, a priority
> dropdown, and an "Overdue only" toggle. It must call `GET /tasks` with query
> parameters (not filter locally), debounce the search input, keep all three
> columns visible, and preserve the loading/empty/error states.

**Result / decision:** Accepted. **Edited** the search handler to debounce at
250 ms rather than firing a request on every keystroke.

### Prompt 2.3 — tests for search and combinations

> Write pytest tests for: search matches title, search matches description,
> case-insensitive search, no-match returns 200 `[]`, combine status + priority,
> and combine search + priority. One PATCH/GET per test, assert status code and the
> returned items.

**Result / decision:** Accepted. Verified each assertion checks the specific
returned task, not merely that "something" came back.

---

## Notes on the review habit

For every accepted block I re-ran `pytest tests/ -v` and, for the endpoints, a live
`curl` check. The two edits above (the `Done` exemption and the search debounce)
came directly from reading the draft before running it, not from a failing test —
which is the point of inspecting AI output rather than trusting it.
