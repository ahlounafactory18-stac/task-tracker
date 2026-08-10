# Project Overview

## What this project is

**Task Tracker** is a small full-stack task-management application built for the
AUB *AI-Assisted Coding* course (Modules 1–3 plus the mid-course project). It lets
a team work from a single shared task list rendered as a Kanban board, with due
dates, an overdue indicator, text search, and combinable filters.

It is intentionally scoped as a **learning project**: a Python/FastAPI backend with
an **in-memory** store (no database) and a single-file **vanilla HTML/CSS/JavaScript**
frontend. There are no user accounts and no persistence layer by design.

## Goals

- Demonstrate a clean, layered backend with a strict data contract.
- Enforce business rules (status transitions, overdue computation) on the **server**,
  which is the trusted boundary — the UI can only hint at valid actions.
- Show a disciplined, test-first workflow where AI-generated code is always
  reviewed, run, and "break-tested" before acceptance.

## Non-goals (explicitly out of scope)

- Persistence / databases (data is lost on restart — this is intended).
- Authentication, authorization, or multi-user accounts.
- Deployment to a public, internet-facing environment.
- New product features beyond the Module 1–3 baseline and the two mid-course
  features (due dates + overdue filter, search + combined filters).

## Primary user & core stories

The primary role is a **team member** working from one shared list. The core user
stories (see `docs/midcourse/user-stories.md`) are:

1. Create, view, update, and delete tasks.
2. Move a task through a controlled lifecycle: `ToDo → InProgress → Done`, with
   `Done → InProgress` reopen. All other transitions are rejected.
3. Set an optional due date and see overdue tasks flagged.
4. Search by keyword and combine search with status/priority/overdue filters.

## Feature summary

- REST API: five CRUD endpoints on `/tasks` plus `/health`.
- Strict Pydantic v2 models: enums for status/priority, title validation,
  rejection of unknown/server-managed fields.
- Status-transition rules enforced in the backend.
- Server-computed "overdue" (never stored), with a matching client-side pill.
- Case-insensitive substring search over title/description, combinable (AND) with
  status, priority, and overdue filters — all on the same `GET /tasks` route.
- Kanban frontend: three columns, priority sorting, drag-and-drop status changes
  with optimistic update and rollback, create/edit modal, and loading / empty /
  ready / error states.

## Technology stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.10+ (developed on 3.12; also runs on 3.14) |
| Web framework | FastAPI |
| Validation | Pydantic v2 |
| ASGI server | Uvicorn |
| Config loading | python-dotenv |
| Tests | pytest + httpx (FastAPI `TestClient`) |
| Frontend | Vanilla HTML / CSS / JavaScript (no build step) |

## Repository map

```
app/               FastAPI backend (routes, models, storage, business rules)
frontend/          single-file Kanban board (index.html)
tests/             pytest suite + model verification script
docs/              this documentation set + midcourse/ history
.github/workflows/ CI pipeline
Dockerfile         container build for the backend
requirements.txt   Python dependencies
```

See `docs/architecture.md` for how these layers fit together.
