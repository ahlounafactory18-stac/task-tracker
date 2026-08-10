# Task Tracker

A small full-stack **Task Tracker** built for the AUB *AI-Assisted Coding* course
(Modules 1–3 + mid-course project). It pairs a Python/**FastAPI** backend (in-memory
store, strict Pydantic v2 validation, server-enforced business rules) with a
dependency-free **vanilla HTML/CSS/JavaScript** Kanban frontend.

> **Scope:** a local, single-user learning project. No database, no authentication —
> both are intentional. See [`docs/release_readiness_report.md`](docs/release_readiness_report.md)
> for what would be required before any public deployment.

**Status:** 37 tests passing · CI configured · Docker-ready.

---

## Table of contents

- [Project overview](#project-overview)
- [Features](#features)
- [Architecture overview](#architecture-overview)
- [Folder structure](#folder-structure)
- [Installation](#installation)
- [Local development setup](#local-development-setup)
- [Running the backend](#running-the-backend)
- [Running the frontend](#running-the-frontend)
- [Running the tests](#running-the-tests)
- [Docker usage](#docker-usage)
- [CI workflow](#ci-workflow)
- [API reference](#api-reference)
- [Documentation](#documentation)
- [Troubleshooting](#troubleshooting)

---

## Project overview

Task Tracker lets a team member manage a single shared task list on a Kanban board.
Tasks move through a controlled lifecycle (`ToDo → InProgress → Done`, with reopen),
can carry an optional due date that drives an "overdue" indicator, and can be searched
and filtered. All rules are enforced on the **backend** — the UI only hints at what is
valid. Full context in [`docs/project_overview.md`](docs/project_overview.md).

## Features

- REST API: five CRUD endpoints on `/tasks` plus `/health`.
- Strict Pydantic v2 models — enums, title validation, rejection of unknown and
  server-managed fields (`extra="forbid"`).
- Server-enforced status-transition rules.
- **Due dates + overdue filter** — optional `due_date`; overdue is *computed, never
  stored* (due before today AND not `Done`); overdue pill on cards.
- **Search + combined filters** — case-insensitive substring search over
  title/description, combinable (AND) with status, priority, and overdue on one
  `GET /tasks` route.
- Kanban frontend — three columns, priority sorting, drag-and-drop with optimistic
  update and rollback, create/edit modal, and loading / empty / ready / error states.
- pytest suite (37 tests) + an 8-check model verification script.

## Architecture overview

Two tiers. The backend owns validation and business rules; the frontend is a static
page that calls the API.

```
Frontend (browser)                         Backend (FastAPI)
frontend/index.html   ── fetch / JSON ──▶   main.py           routes, CORS, status codes
  Kanban board                               business_rules.py transitions, is_overdue
  filter bar, modal   ◀── JSON / status ──   storage.py        in-memory dict store
  optimistic drag                            models.py         Pydantic v2 contract
```

Backend dependency flow is one-directional: `main → {business_rules, storage} → models`.
Details and data-flow examples in [`docs/architecture.md`](docs/architecture.md).

## Folder structure

```
task-tracker/                  # project root (run all commands from here)
├── app/                       # FastAPI backend
│   ├── __init__.py
│   ├── main.py                # app, CORS, /health + 5 CRUD routes
│   ├── models.py              # Pydantic v2 models + enums
│   ├── storage.py             # in-memory store + _reset (validate-before-commit)
│   └── business_rules.py      # VALID_TRANSITIONS, validate_status_transition, is_overdue
├── frontend/
│   └── index.html             # vanilla Kanban board + modal (no build step)
├── tests/
│   ├── conftest.py            # TestClient + autouse storage reset
│   ├── verify_a.py            # 8 model checks (python -m tests.verify_a)
│   ├── test_tasks.py          # baseline API tests
│   └── test_midcourse.py      # due-date / overdue / search / combined-filter tests
├── docs/                      # release + architecture + review documentation
│   ├── project_overview.md    architecture.md          testing_strategy.md
│   ├── code_review.md         security_review.md       deployment_guide.md
│   ├── ai_usage_report.md     dependency_review.md     release_readiness_report.md
│   └── midcourse/             # mid-course history (stories, ADR, prompts, verification)
├── .github/workflows/ci.yml   # CI: install + verify + pytest, fail on test failure
├── Dockerfile                 # backend container image
├── .dockerignore
├── .env.example               # non-sensitive config template
├── .gitignore
├── requirements.txt
├── README.md
└── AGENTS.md                  # guidance for AI agents & future maintainers
```

> **Note on nesting:** in this repository the project root shown above is nested one
> level deep (`task-tracker/task-tracker/`). Run all commands, CI, and Docker builds
> from the **inner** directory that contains `app/` and `tests/`.

## Installation

Requirements: **Python 3.10+** (developed on 3.12; also runs on 3.14).

```bash
# from the project root
python -m venv venv

# activate it
source venv/bin/activate        # Linux / macOS
venv\Scripts\activate           # Windows PowerShell

pip install -r requirements.txt
```

## Local development setup

Copy the environment template (optional — the app runs without it):

```bash
cp .env.example .env            # Linux / macOS
copy .env.example .env          # Windows PowerShell
```

`.env` holds only non-sensitive settings (`PORT`, `APP_ENV`) and is git-ignored. This
project stores no secrets.

## Running the backend

```bash
uvicorn app.main:app --reload --port 8000
```

- Health check: <http://localhost:8000/health>
- Swagger UI: <http://localhost:8000/docs>

```bash
curl http://localhost:8000/health
# {"status":"ok","timestamp":"..."}
```

## Running the frontend

`frontend/index.html` is a single static file that calls the API at
`http://localhost:8000` (set by `BASE_URL` near the top of the file). Serve it from a
local static server so the browser origin is `http://localhost` (CORS allows any
localhost port):

```bash
# from the project root, in a second terminal
python -m http.server 5500
# then open http://localhost:5500/frontend/index.html
```

Or, in VS Code, right-click `frontend/index.html` → **Open with Live Server**
(default <http://localhost:5500/frontend/index.html>). Keep the backend running in the
first terminal.

## Running the tests

```bash
# full API suite (37 tests)
pytest tests/ -v

# model verification script (8 checks; exits non-zero on failure)
python -m tests.verify_a
```

**Break Test (optional).** To confirm the tests protect real behavior, temporarily
break production code and re-run pytest:

1. In `app/main.py`, disable the `validate_status_transition` check in PATCH → the
   invalid-transition and same-status tests should fail.
2. In `app/models.py`, make the blank-title check ineffective → the blank-title test
   should fail.

Restore the code and confirm the suite is green again. Full strategy, coverage gaps,
and recommended unit tests: [`docs/testing_strategy.md`](docs/testing_strategy.md).

## Docker usage

The provided `Dockerfile` runs the **backend** API (stateless — the in-memory store is
cleared when the container stops).

```bash
# build (from the project root)
docker build -t task-tracker:latest .

# run
docker run --rm -p 8000:8000 task-tracker:latest

# verify
curl http://localhost:8000/health
```

Override the port with `-e PORT=8080 -p 8080:8080`. The image runs as a non-root user
and includes a `/health` HEALTHCHECK. To use the board against the container, serve
`frontend/index.html` locally as above. Full guide:
[`docs/deployment_guide.md`](docs/deployment_guide.md).

## CI workflow

`.github/workflows/ci.yml` runs on every push and pull request:

1. Checks out the repo.
2. Sets up Python (matrix: **3.10, 3.11, 3.12**).
3. Installs dependencies from `requirements.txt` (verifies a clean install).
4. Runs the model verification script (`python -m tests.verify_a`).
5. Runs the full suite (`pytest tests/ -v`).
6. **Fails the build if any test fails**, so a red suite blocks a merge.

If the nested layout is preserved, ensure the workflow runs from the inner
`task-tracker/` (the directory with `app/` and `tests/`) — add a `working-directory`
or `defaults.run.working-directory` if you relocate the workflow.

## API reference

`GET /tasks` filters combine with **AND** semantics:

- `status=ToDo|InProgress|Done`
- `priority=Low|Medium|High`
- `overdue=true|false` (server-computed: due before today and not `Done`)
- `q=<text>` (case-insensitive substring over title and description)

Example: `GET /tasks?q=report&priority=High&overdue=true`

| Method | Path | Success | Errors |
|--------|------|---------|--------|
| GET | `/health` | 200 | — |
| POST | `/tasks` | 201 | 422 |
| GET | `/tasks` | 200 | 422 (bad filter) |
| GET | `/tasks/{id}` | 200 | 404 |
| PATCH | `/tasks/{id}` | 200 | 404, 422 |
| DELETE | `/tasks/{id}` | 204 (empty) | 404 |

## Documentation

| Document | Purpose |
|----------|---------|
| [`AGENTS.md`](AGENTS.md) | Guidance for AI agents & future maintainers |
| [`docs/project_overview.md`](docs/project_overview.md) | Goals, scope, stack |
| [`docs/architecture.md`](docs/architecture.md) | Layers, data flow, decisions |
| [`docs/testing_strategy.md`](docs/testing_strategy.md) | Coverage, gaps, manual checklist |
| [`docs/code_review.md`](docs/code_review.md) | Strengths, weaknesses, tech debt |
| [`docs/security_review.md`](docs/security_review.md) | Secrets, validation, CORS, deps |
| [`docs/deployment_guide.md`](docs/deployment_guide.md) | Local, Docker, CI, prod gates |
| [`docs/dependency_review.md`](docs/dependency_review.md) | Dependency risks & pinning |
| [`docs/ai_usage_report.md`](docs/ai_usage_report.md) | AI governance & ownership |
| [`docs/release_readiness_report.md`](docs/release_readiness_report.md) | Final go/no-go |

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| Frontend shows the error state | Backend not running | Start the backend; click **Retry** |
| CORS error in the browser console | Frontend opened as `file://` | Serve via a local static server (`http://localhost`) |
| `pip install` fails | Old pip / wrong Python | `python -m pip install --upgrade pip`; use Python 3.10+ |
| `uvicorn: command not found` | venv not activated | Activate the venv, reinstall requirements |
| Port 8000 already in use | Another process bound it | Use another port (`--port 8001`) and update the frontend `BASE_URL` |
| Tasks vanish after restart | In-memory store (by design) | Expected; there is no persistence |
| `docker run` exits immediately | Port already in use | Map a different host port: `-p 8080:8000` |
| Tests pass locally, fail in CI | Python/dependency drift | Match CI's Python matrix; consider pinning deps |
| `StarletteDeprecationWarning` (httpx) | Newer httpx/starlette | Harmless; tracked in `docs/dependency_review.md` |
