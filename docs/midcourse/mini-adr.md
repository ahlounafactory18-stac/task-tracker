# Mini-ADR — Mid-course features

## Context

The Modules 1–3 baseline is a FastAPI Task Tracker with an in-memory store, a
strict Pydantic v2 model layer, status-transition rules, and a vanilla Kanban
frontend. The mid-course project adds two scoped features without new frameworks,
databases, or dependencies.

## Decision

**Feature 1 — Due dates + overdue filter.** Add a single optional field
`due_date: date | None` to `TaskCreate`, `TaskUpdate`, and `TaskResponse`. Pydantic
parses ISO dates and rejects malformed input with 422, so no custom date validator
is needed. "Overdue" is **computed, not stored**: a helper
`is_overdue(due_date, status, today=None)` in `business_rules.py` returns `True`
when the due date is strictly before today and the status is not `Done`. The
`GET /tasks` endpoint gains an `overdue: bool | None` filter that uses this helper.
The frontend computes the same rule in JavaScript to show an "Overdue" pill.

**Feature 2 — Search + combined filters.** Extend the existing `GET /tasks`
endpoint with a `q: str | None` parameter that performs a case-insensitive
substring match over title and description. `q` combines with the existing
`status`, `priority`, and new `overdue` filters using AND semantics. No new
endpoint and no data-model change. The frontend adds a compact filter bar that
builds a query string and calls `GET /tasks`, so the columns stay visible and
empty/error states are preserved.

Both features live in the same `GET /tasks` query path, which keeps the change
surface small and the filter tests cohesive.

## Alternatives the AI suggested, and what was rejected

- **Store `overdue` as a boolean column.** Rejected: it is derived data and would
  go stale the moment a due date passes or a task is completed. Computing it keeps
  a single source of truth.
- **Add a dedicated `/search` endpoint.** Rejected: out of Module scope and
  redundant. Extending `GET /tasks` reuses the existing filter pipeline.
- **Client-side-only filtering** of the loaded task array. Rejected: it would leave
  the backend search untested and violate the "extend `GET /tasks`" requirement.
- **Full-text search / database index / SQLite migration.** Rejected: no database
  is in Modules 1–3 scope. A substring scan over an in-memory list is adequate for
  a learning project.
- **Tags/labels and comments features.** Considered but not selected: they add more
  data-model surface and endpoints than the two chosen features.

## Consequences and risks if the project grew

- Substring search is O(n) per request. At larger scale this would need indexing or
  pagination.
- `is_overdue` uses the server's local `date.today()`. A production system with
  users in multiple time zones would need explicit time-zone handling.
- In-memory storage means all data (including due dates) is lost on restart, which
  is acceptable only for this learning scope.
