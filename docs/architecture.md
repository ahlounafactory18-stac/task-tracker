# Architecture

## Overview

Task Tracker is a two-tier application:

- a **backend** HTTP API (FastAPI) that owns all validation and business rules, and
- a **frontend** single-page Kanban board (static HTML/CSS/JS) that talks to the
  API over `fetch`.

There is no database. State lives in a process-local Python dictionary and is lost
when the server restarts. This is a deliberate Module 1–3 scope decision.

```
┌────────────────────────┐        HTTP (fetch / JSON)        ┌───────────────────────────────┐
│   Frontend (browser)   │  ───────────────────────────────▶ │        Backend (FastAPI)       │
│  frontend/index.html   │                                    │                               │
│  - Kanban board        │  ◀─────────────────────────────── │  main.py  (routes, CORS)      │
│  - modal, filter bar   │        JSON responses / status     │  models.py (Pydantic contract)│
│  - optimistic drag/drop│                                    │  business_rules.py (rules)    │
└────────────────────────┘                                    │  storage.py (in-memory store) │
                                                              └───────────────────────────────┘
```

## Backend layering

The backend is split into four modules with a strict, one-directional dependency
flow. Nothing lower ever imports something higher.

```
main.py            HTTP layer: routing, status codes, CORS, error mapping
   │  depends on
   ▼
business_rules.py  pure domain logic: status transitions, is_overdue
storage.py         persistence layer: in-memory dict, id generation
   │  both depend on
   ▼
models.py          data contract: Pydantic models + enums (no dependencies)
```

### `app/models.py` — the data contract

The single source of truth for what a task is. Everything else is built on it.

- `TaskStatus`, `TaskPriority` — string enums; never free-form strings.
- `TaskCreate` — client input for creation. `extra="forbid"` rejects unknown and
  server-managed fields (`id`, `created_at`, `updated_at`). Title is validated
  (non-blank, ≤ 200 chars after stripping).
- `TaskUpdate` — client input for PATCH. Every field optional; same forbidding of
  extra fields; title validated only when present.
- `TaskResponse` — the API output shape, including server-generated fields.

**Design rule:** input models and output models are separate. Clients can never
set server-managed fields, and the response shape is explicit.

### `app/storage.py` — in-memory persistence

- A module-level `dict[int, dict]` keyed by an auto-incrementing integer id, plus a
  monotonic `_next_id` counter (starts at 1, never reused).
- Records are stored as plain dicts and only converted to `TaskResponse` on the way
  out, so every returned value is validated and callers cannot mutate the store by
  holding a reference.
- **`update_task` validates before it commits:** it merges existing record + changes
  into a *temporary* copy, constructs a `TaskResponse` from it (which raises on
  invalid data), and only writes back on success. A rejected update therefore leaves
  the store completely unchanged — it can never be corrupted by bad input.
- `_reset()` clears the store and counter, giving tests a deterministic start.

### `app/business_rules.py` — domain logic (pure functions)

- `VALID_TRANSITIONS` — the exact allowed `(current, new)` status pairs:
  `ToDo→InProgress`, `InProgress→Done`, `Done→InProgress`. Everything else (skips,
  reverts, same-to-same no-ops) is rejected.
- `validate_status_transition(current, new)` — checks the *pair*, not just whether
  `new` is a valid enum.
- `is_overdue(due_date, status, today=None)` — a task is overdue when its due date
  is strictly before today **and** its status is not `Done`. `today` is injectable
  so tests are deterministic. Overdue is **computed, never stored**, so it can never
  go stale.

### `app/main.py` — HTTP layer

Wires the layers into routes and owns HTTP semantics:

| Method | Path | Success | Errors |
|--------|------|---------|--------|
| GET | `/health` | 200 (status + UTC timestamp) | — |
| POST | `/tasks` | 201 (created task) | 422 (invalid body) |
| GET | `/tasks` | 200 (list, possibly `[]`) | 422 (invalid filter enum) |
| GET | `/tasks/{id}` | 200 | 404 |
| PATCH | `/tasks/{id}` | 200 | 404, 422 (invalid transition/body) |
| DELETE | `/tasks/{id}` | 204 (empty body) | 404 |

Two ordering decisions matter and are covered by tests:

1. **Existence before transition:** PATCH checks the task exists (404) *before*
   validating the status transition (422). A missing id never returns 422.
2. **Storage-layer validation surfaced as 422:** if an invalid value slips past the
   input model (e.g. a raw `{"title": null}`), `update_task` raises
   `ValidationError`, which `main.py` re-raises as `RequestValidationError` so the
   client sees a standard 422 rather than an unhandled 500.

## CORS

`main.py` allows any `http://localhost` / `http://127.0.0.1` origin (any port) via
`allow_origin_regex`. This exists so the static frontend served from a local static
server (e.g. Live Server on `:5500`) can call the API on `:8000` without port-mismatch
CORS failures. It is scoped to localhost only and must be tightened before any
non-local deployment (see `docs/security_review.md`).

## Frontend

`frontend/index.html` is a single, dependency-free file (HTML + CSS + JS). Key
behaviors:

- `BASE_URL = "http://localhost:8000"` — the API origin (hardcoded).
- `fetchTasks()` builds a query string from the filter bar (search is debounced at
  250 ms) and renders three columns, sorting cards High → Medium → Low.
- Drag-and-drop issues a PATCH with an **optimistic** UI update and **rolls back** on
  a rejected transition, showing the server's message.
- A create/edit modal validates the title client-side and sends a **diff-based**
  PATCH (only changed fields) so editing a task never triggers a same-status 422.
- Distinct loading / empty / ready / error states, with a retry action when the
  backend is unreachable.

The frontend re-computes the overdue rule client-side only for display (the pill);
the backend remains the authority for filtering.

## Data flow example — creating a task

1. User submits the modal → `fetch POST /tasks` with a JSON body.
2. FastAPI parses the body into `TaskCreate` (validates title, defaults, rejects
   extras). Invalid → 422 returned to the modal, which shows the error.
3. `storage.add_task` assigns an id and timestamps, stores the record, returns a
   `TaskResponse`.
4. `main.py` returns 201 with the created task; the frontend re-fetches and
   re-renders the board.

## Key architectural decisions

- **Server is the trusted boundary.** All rules live in the backend; the UI only
  hints. A direct API caller cannot bypass them.
- **Derived data is computed, not stored** (`overdue`), keeping a single source of
  truth.
- **Validate-before-commit** in storage guarantees the store is never left in a
  corrupt state.
- **Separate input/output models** keep the client from ever setting server-managed
  fields.

See `docs/midcourse/mini-adr.md` for the mid-course feature decision record.
