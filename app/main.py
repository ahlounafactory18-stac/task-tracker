"""Task Tracker API — FastAPI application and routes.

Wires the model, storage, and business-rule layers into an HTTP API:
- GET  /health              health check with a timestamp
- POST /tasks               create a task (201)
- GET  /tasks               list tasks, optional status/priority filters (200)
- GET  /tasks/{id}          fetch one task (200 / 404)
- PATCH /tasks/{id}         partial update, enforces status transitions (200 / 404 / 422)
- DELETE /tasks/{id}        delete a task (204 empty body / 404)

CORS is enabled for local frontend origins so the browser Kanban board can call
the API during development.
"""

from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware

from app import storage
from app.business_rules import is_overdue, validate_status_transition
from app.models import TaskCreate, TaskPriority, TaskResponse, TaskStatus, TaskUpdate

app = FastAPI(title="Task Tracker API", version="1.0.0")

# Allow any localhost / 127.0.0.1 port (e.g. Live Server on 5500). Local-only,
# so it stays safe for a learning project while avoiding port-mismatch CORS pain.
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    """Liveness check. Returns status and a current UTC timestamp."""
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}


@app.post("/tasks", response_model=TaskResponse, status_code=201)
def create_task(payload: TaskCreate) -> TaskResponse:
    """Create a task and return it with server-generated fields (201)."""
    return storage.add_task(payload)


@app.get("/tasks", response_model=list[TaskResponse])
def list_tasks(
    status: TaskStatus | None = None,
    priority: TaskPriority | None = None,
    overdue: bool | None = None,
    q: str | None = None,
) -> list[TaskResponse]:
    """List tasks. All filters combine with AND semantics.

    - ``status`` / ``priority``: exact enum match (invalid values -> 422).
    - ``overdue``: server-computed; ``true`` returns only overdue tasks,
      ``false`` only non-overdue tasks.
    - ``q``: case-insensitive substring search over title and description.

    An empty result is a normal 200 with ``[]``.
    """
    tasks = storage.get_all_tasks()
    if status is not None:
        tasks = [t for t in tasks if t.status == status]
    if priority is not None:
        tasks = [t for t in tasks if t.priority == priority]
    if overdue is not None:
        tasks = [t for t in tasks if is_overdue(t.due_date, t.status) == overdue]
    if q is not None and q.strip():
        needle = q.strip().lower()
        tasks = [
            t for t in tasks
            if needle in t.title.lower() or needle in t.description.lower()
        ]
    return tasks


@app.get("/tasks/{task_id}", response_model=TaskResponse)
def get_task(task_id: int) -> TaskResponse:
    """Return one task, or 404 if it does not exist."""
    task = storage.get_task_by_id(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@app.patch("/tasks/{task_id}", response_model=TaskResponse)
def update_task(task_id: int, payload: TaskUpdate) -> TaskResponse:
    """Partially update a task.

    Order matters: existence is checked first (404 before any 422), then the
    status transition is validated only when a status change is actually
    requested. Title-only or description-only updates skip transition checks.
    """
    existing = storage.get_task_by_id(task_id)
    if existing is None:
        raise HTTPException(status_code=404, detail="Task not found")

    changes = payload.model_dump(exclude_unset=True)

    if "status" in changes and payload.status is not None:
        if not validate_status_transition(existing.status, payload.status):
            raise HTTPException(
                status_code=422,
                detail=(
                    f"Invalid status transition: "
                    f"{existing.status.value} -> {payload.status.value}"
                ),
            )

    return storage.update_task(task_id, changes)


@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int) -> Response:
    """Delete a task. Returns 204 with an empty body, or 404 if missing."""
    if not storage.delete_task(task_id):
        raise HTTPException(status_code=404, detail="Task not found")
    return Response(status_code=204)
