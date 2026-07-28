"""In-memory storage layer for the Task Tracker.

This is a deliberately simple, process-local store: a dict keyed by integer id
plus a monotonic id counter. There is no database and no persistence — restarting
the server empties the store. That is the intended Module 1–3 scope.

Design contract:
- ``id`` values are server-generated, start at 1, and are never reused.
- ``created_at`` is set once; ``updated_at`` is bumped on every update.
- Helpers return freshly built ``TaskResponse`` objects, so callers can never
  mutate the internal store by holding on to a returned value.
- ``_reset`` clears the store and the counter, giving tests a clean, deterministic
  starting point (ids begin at 1 again).
"""

from datetime import datetime, timezone

from app.models import TaskCreate, TaskResponse

# Internal state. Records are stored as plain dicts and only converted to
# TaskResponse on the way out, so every returned object is validated and typed.
_tasks: dict[int, dict] = {}
_next_id: int = 1


def _now() -> datetime:
    """Return the current time as a timezone-aware UTC timestamp."""
    return datetime.now(timezone.utc)


def add_task(payload: TaskCreate) -> TaskResponse:
    """Store a new task and return it with server-generated fields.

    Assigns the next integer id and sets ``created_at``/``updated_at`` to the
    same moment. The incoming payload has already been validated by the model.
    """
    global _next_id
    now = _now()
    record = {
        "id": _next_id,
        "title": payload.title,
        "description": payload.description,
        "status": payload.status,
        "priority": payload.priority,
        "assignee": payload.assignee,
        "due_date": payload.due_date,
        "created_at": now,
        "updated_at": now,
    }
    _tasks[_next_id] = record
    _next_id += 1
    return TaskResponse(**record)


def get_all_tasks() -> list[TaskResponse]:
    """Return all tasks in insertion (creation) order."""
    return [TaskResponse(**record) for record in _tasks.values()]


def get_task_by_id(task_id: int) -> TaskResponse | None:
    """Return the task with ``task_id``, or ``None`` if it does not exist."""
    record = _tasks.get(task_id)
    return TaskResponse(**record) if record is not None else None


def update_task(task_id: int, changes: dict) -> TaskResponse | None:
    """Apply a partial update to an existing task.

    ``changes`` should contain only the fields the caller wants to change
    (typically ``TaskUpdate.model_dump(exclude_unset=True)``). Unlisted fields
    are left untouched. ``updated_at`` is refreshed. Returns the updated task,
    or ``None`` if no task has that id. Rebuilding a ``TaskResponse`` re-validates
    and coerces the merged record, so type integrity is preserved.
    """
    record = _tasks.get(task_id)
    if record is None:
        return None
    for key, value in changes.items():
        record[key] = value
    record["updated_at"] = _now()
    return TaskResponse(**record)


def delete_task(task_id: int) -> bool:
    """Delete a task. Return ``True`` if it existed, ``False`` otherwise."""
    return _tasks.pop(task_id, None) is not None


def _reset() -> None:
    """Clear all tasks and reset the id counter. Intended for tests."""
    global _next_id
    _tasks.clear()
    _next_id = 1
