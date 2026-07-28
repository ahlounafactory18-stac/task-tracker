"""Pydantic v2 data models for the Task Tracker API.

This module is the data contract every endpoint is built on. If the model is
loose, every endpoint inherits the mistake, so the rules here are strict:

- ``TaskStatus`` / ``TaskPriority`` are enums, never free strings.
- ``TaskCreate`` / ``TaskUpdate`` are client input models. They forbid extra
  fields and therefore reject server-managed fields (``id``, ``created_at``,
  ``updated_at``) if a client tries to send them.
- ``TaskResponse`` is what the API returns, including server-generated fields.

Pydantic v2 syntax only: ``ConfigDict``, ``@field_validator``. No v1 patterns
(no inner ``class Config``, no ``.dict()`` at the call sites).
"""

from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, field_validator

# Maximum allowed length of a task title, measured after stripping whitespace.
MAX_TITLE_LENGTH = 200


class TaskStatus(str, Enum):
    """Allowed task statuses. Values are exact and case-sensitive."""

    ToDo = "ToDo"
    InProgress = "InProgress"
    Done = "Done"


class TaskPriority(str, Enum):
    """Allowed task priorities. ``Medium`` is the default used on create."""

    Low = "Low"
    Medium = "Medium"
    High = "High"


def _clean_title(value: str) -> str:
    """Normalise and validate a title.

    Strips surrounding whitespace, rejects empty/whitespace-only titles, and
    rejects titles longer than ``MAX_TITLE_LENGTH`` after stripping. Returns the
    stripped title so the stored value is always normalised.
    """
    stripped = value.strip()
    if not stripped:
        raise ValueError("Title is required and cannot be blank")
    if len(stripped) > MAX_TITLE_LENGTH:
        raise ValueError(f"Title cannot exceed {MAX_TITLE_LENGTH} characters")
    return stripped


class TaskCreate(BaseModel):
    """Client payload for creating a task.

    Only ``title`` is required. ``status``/``priority`` fall back to their
    defaults, ``description`` defaults to an empty string, and ``assignee`` is
    optional. ``extra="forbid"`` means any unexpected field (including ``id`` or
    timestamps) is rejected with a validation error.
    """

    model_config = ConfigDict(extra="forbid")

    title: str
    description: str = ""
    status: TaskStatus = TaskStatus.ToDo
    priority: TaskPriority = TaskPriority.Medium
    assignee: str | None = None
    due_date: date | None = None  # optional; Pydantic rejects malformed dates with 422

    @field_validator("title")
    @classmethod
    def _validate_title(cls, value: str) -> str:
        return _clean_title(value)


class TaskUpdate(BaseModel):
    """Client payload for a partial update (PATCH).

    Every editable field is optional so callers can send just the fields they
    want to change. Server-managed fields are not defined here and, combined
    with ``extra="forbid"``, cannot be set by the client. A provided title is
    still validated; an omitted title is left untouched.
    """

    model_config = ConfigDict(extra="forbid")

    title: str | None = None
    description: str | None = None
    status: TaskStatus | None = None
    priority: TaskPriority | None = None
    assignee: str | None = None
    due_date: date | None = None

    @field_validator("title")
    @classmethod
    def _validate_optional_title(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _clean_title(value)


class TaskResponse(BaseModel):
    """Task shape returned by the API, including server-generated fields."""

    id: int
    title: str
    description: str
    status: TaskStatus
    priority: TaskPriority
    assignee: str | None
    due_date: date | None
    created_at: datetime
    updated_at: datetime
