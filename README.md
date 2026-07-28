# Task Tracker

A small Task Tracker built for the AUB AI-Assisted Coding course (Modules 1–3).
It has a Python/FastAPI backend with an in-memory store and a vanilla
HTML/CSS/JavaScript Kanban frontend.

## Features

- REST API with five CRUD endpoints plus `/health`
- Strict Pydantic v2 models (enums, validation, extra-field rejection)
- Status-transition business rules enforced in the backend
- Kanban board with three columns, priority sorting, and loading / empty /
  ready / error states
- Drag-and-drop status changes with optimistic update and rollback on rejection
- Create / edit modal with client-side title validation and server-error display
- **Due dates + overdue filter** (mid-course): optional `due_date`, server-computed
  overdue filter, and an "Overdue" pill on cards (completed tasks are never overdue)
- **Search + combined filters** (mid-course): case-insensitive text search over
  title/description, combinable with priority and overdue filters via `GET /tasks`
- pytest suite plus a model verification script

## Requirements

- Python 3.10+ (developed on 3.12)

## Setup

```bash
# from the project root
python -m venv venv

# activate it
source venv/bin/activate        # Linux / macOS
venv\Scripts\activate           # Windows PowerShell

pip install -r requirements.txt
# Optional: record exact resolved versions
pip freeze
```

Copy the example environment file if you want to load environment variables:

```bash
cp .env.example .env            # Linux / macOS
copy .env.example .env          # Windows PowerShell
```

## Run the backend

```bash
uvicorn app.main:app --reload --port 8000
```

- Health check: <http://localhost:8000/health>
- Swagger UI: <http://localhost:8000/docs>

Quick health check with curl:

```bash
curl http://localhost:8000/health
# {"status":"ok","timestamp":"..."}
```

## Open the frontend

The frontend is a single static file at `frontend/index.html` that calls the API
at `http://localhost:8000`.

Serve it from a local static server so the browser origin is a normal
`http://localhost` origin (CORS allows any localhost port). With VS Code Live
Server, right-click `frontend/index.html` and choose "Open with Live Server"
(default <http://localhost:5500/frontend/index.html>).

Or use Python's built-in server:

```bash
# from the project root, in a second terminal
python -m http.server 5500
# then open http://localhost:5500/frontend/index.html
```

Keep the backend running in the first terminal while you use the board.

## Run the tests

```bash
# model checks (8 checks)
python -m tests.verify_a

# full API test suite
pytest tests/ -v
```

### Break Test (optional)

To confirm the tests protect real behavior, temporarily break production code and
re-run pytest:

1. In `app/main.py`, disable the `validate_status_transition` check in the PATCH
   route → the invalid-transition and same-status tests should fail.
2. In `app/models.py`, make the blank-title check ineffective → the blank-title
   test should fail.

Restore the code afterward and confirm the suite is green again.

## Project layout

```
app/
  main.py            FastAPI app, CORS, /health + 5 CRUD routes
  models.py          Pydantic v2 models + enums
  storage.py         in-memory store + _reset
  business_rules.py  VALID_TRANSITIONS + validate_status_transition
frontend/
  index.html         vanilla Kanban board + modal
tests/
  conftest.py        TestClient + autouse storage reset
  verify_a.py        8 model checks
  test_tasks.py      baseline API tests
  test_midcourse.py  due-date / overdue / search / combined-filter tests
docs/
  midcourse/         mid-course documentation (stories, ADR, prompts, verification, reflection)
```

## API query parameters (GET /tasks)

All filters combine with AND semantics:

- `status=ToDo|InProgress|Done`
- `priority=Low|Medium|High`
- `overdue=true|false` (server-computed: due date before today and not Done)
- `q=<text>` (case-insensitive substring over title and description)

Example: `GET /tasks?q=report&priority=High&overdue=true`
