"""Status-transition business rules for the Task Tracker.

The backend is the trusted enforcement point for status changes. UI buttons can
hide invalid actions, but a client can still call the API directly, so the rule
lives here and the PATCH route calls it.

Allowed transitions:
    ToDo        -> InProgress   (work has started)
    InProgress  -> Done         (work is finished)
    Done        -> InProgress   (a completed task can be reopened)

Everything else is rejected, including "skip" moves (ToDo -> Done), reverting to
the beginning (Done -> ToDo), and same-to-same no-ops (e.g. ToDo -> ToDo).
"""

from datetime import date

from app.models import TaskStatus

# Exact set of allowed (current, new) pairs. Same-to-same pairs are intentionally
# absent, so no-op status changes are rejected.
VALID_TRANSITIONS: frozenset[tuple[TaskStatus, TaskStatus]] = frozenset(
    {
        (TaskStatus.ToDo, TaskStatus.InProgress),
        (TaskStatus.InProgress, TaskStatus.Done),
        (TaskStatus.Done, TaskStatus.InProgress),
    }
)


def validate_status_transition(current: TaskStatus, new: TaskStatus) -> bool:
    """Return True if moving from ``current`` to ``new`` is allowed.

    Checks the *pair*, not merely whether ``new`` is a valid enum value. Because
    same-to-same pairs are not in ``VALID_TRANSITIONS``, they return False.
    """
    return (current, new) in VALID_TRANSITIONS


def is_overdue(
    due_date: date | None,
    status: TaskStatus,
    today: date | None = None,
) -> bool:
    """Return True if a task is overdue.

    A task is overdue when it has a due date strictly before today AND is not
    already Done. Completed tasks are never overdue, and a task due today is not
    yet overdue. ``today`` is injectable so tests are deterministic.
    """
    if due_date is None or status is TaskStatus.Done:
        return False
    reference = today if today is not None else date.today()
    return due_date < reference
