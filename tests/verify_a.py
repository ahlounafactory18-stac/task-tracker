"""Model verification script for Part 2.1.

Run with:  python -m tests.verify_a

Prints PASS/FAIL for each of the eight model checks and exits non-zero if any
check fails, so it can also serve as a quick gate before running the API.
"""

import sys

from pydantic import ValidationError

from app.models import TaskCreate, TaskPriority, TaskStatus, TaskUpdate


def _rejects(build) -> bool:
    """Return True if building the model raises a validation error."""
    try:
        build()
        return False
    except ValidationError:
        return True


def run_checks() -> bool:
    checks = []

    # 1. Whitespace-only title rejected.
    checks.append(("Whitespace-only title rejected",
                   _rejects(lambda: TaskCreate(title="   "))))
    # 2. Empty title rejected.
    checks.append(("Empty title rejected",
                   _rejects(lambda: TaskCreate(title=""))))
    # 3. Title over 200 characters rejected.
    checks.append(("Title over 200 characters rejected",
                   _rejects(lambda: TaskCreate(title="x" * 201))))
    # 4. Defaults applied: status ToDo, priority Medium, empty description.
    task = TaskCreate(title="Write report")
    checks.append(("Defaults applied (ToDo / Medium / empty description)",
                   task.status is TaskStatus.ToDo
                   and task.priority is TaskPriority.Medium
                   and task.description == ""))
    # 5. Extra field rejected on TaskCreate.
    checks.append(("Extra field rejected on TaskCreate",
                   _rejects(lambda: TaskCreate(title="ok", colour="red"))))
    # 6. id rejected on TaskCreate.
    checks.append(("id rejected on TaskCreate",
                   _rejects(lambda: TaskCreate(title="ok", id=5))))
    # 7. created_at rejected on TaskUpdate.
    checks.append(("created_at rejected on TaskUpdate",
                   _rejects(lambda: TaskUpdate(created_at="2024-01-01T00:00:00"))))
    # 8. Invalid status rejected.
    checks.append(("Invalid status rejected",
                   _rejects(lambda: TaskCreate(title="ok", status="Archived"))))

    all_pass = True
    for name, ok in checks:
        all_pass &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {name}")
    return all_pass


if __name__ == "__main__":
    ok = run_checks()
    print("\nAll checks passed." if ok else "\nSome checks FAILED.")
    sys.exit(0 if ok else 1)
