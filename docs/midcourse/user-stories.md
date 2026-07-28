# User Stories

Two features were added to the Task Tracker for the mid-course project:
**Due dates + overdue filter** and **Search + combined filters**. The primary
role is a **team member** working from a single shared task list (Module scope:
no accounts, no per-user lists).

---

## Feature 1 — Due dates + overdue filter

### Story 1.1 — Set a due date on a task
As a team member, I want to set an optional due date when creating a task so that
I can track deadlines.

**Acceptance criteria**
- The due date is optional; a task can be created without one (`due_date` is `null`).
- A valid ISO date (`YYYY-MM-DD`) is accepted and returned unchanged.
- A malformed date (e.g. `not-a-date`) is rejected with HTTP 422.

### Story 1.2 — Reschedule a task
As a team member, I want to change a task's due date so that I can reschedule it.
- A PATCH that sets `due_date` returns 200 and the new value is persisted.
- The change does not require touching status or other fields.

### Story 1.3 — See overdue tasks at a glance
As a team member, I want overdue tasks to stand out on the board so that I can act
on what is late.
- A task is overdue when its due date is strictly before today **and** its status
  is not `Done`.
- Overdue cards show an "Overdue" pill.
- A task due today is **not** overdue.

### Story 1.4 — Filter to only overdue tasks
As a team member, I want to filter the board to only overdue tasks so that I can
focus on what is late.
- `GET /tasks?overdue=true` returns only overdue tasks.
- `GET /tasks?overdue=false` returns only non-overdue tasks.
- All three columns remain visible; empty columns show a placeholder.

**AI assumption corrected:** the assistant's first `is_overdue` implementation
treated *any* task with a past due date as overdue, including completed ones. That
would flag finished work as late. I corrected the rule so a `Done` task is never
overdue, and added `test_completed_task_is_not_overdue` to lock the behavior in.

---

## Feature 2 — Search + combined filters

### Story 2.1 — Search tasks by keyword
As a team member, I want to search tasks by keyword so that I can find a task
without scanning every column.
- `GET /tasks?q=<text>` matches the text against title **or** description.
- Search is case-insensitive and matches substrings.
- No matches returns HTTP 200 with `[]` (not 404).

### Story 2.2 — Combine search with a priority filter
As a team member, I want to combine search with a priority filter so that I can
narrow results precisely.
- Filters combine with AND semantics on the backend.
- `GET /tasks?q=urgent&priority=High` returns only high-priority tasks whose text
  contains "urgent".

### Story 2.3 — Filter by priority
As a team member, I want to filter the board by priority so that I can focus on
the most important work.
- `GET /tasks?priority=High` returns only high-priority tasks.
- An invalid priority value returns HTTP 422.

### Story 2.4 — Keep the board structure while filtering
As a team member, I want the three columns to stay visible while filtering so that
the board still reads as a Kanban.
- All columns render even when a filter narrows results.
- Columns with no matching tasks show an empty-state placeholder.

**AI assumption corrected:** the assistant proposed filtering the already-loaded
task array in the browser (client-side only) and, separately, adding a dedicated
`/search` endpoint. Both were rejected. Client-side-only filtering would leave the
backend feature untested, and a new endpoint is out of Module scope. The filter
bar instead calls the existing `GET /tasks` with query parameters, so filtering is
enforced and tested on the backend.
