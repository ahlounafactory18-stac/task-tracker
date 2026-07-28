"""Mid-course feature tests.

Feature 1: Due dates + overdue filter
Feature 2: Search + combined filters

Storage is reset automatically between tests by the autouse fixture in
conftest.py. Overdue tests build dates relative to the real "today" so they stay
correct whenever the suite runs.
"""

from datetime import date, timedelta

PAST = (date.today() - timedelta(days=2)).isoformat()
FUTURE = (date.today() + timedelta(days=5)).isoformat()


# ======================================================================= #
# Feature 1 — Due dates + overdue filter
# ======================================================================= #
def test_create_with_valid_due_date_returns_201(client):
    response = client.post("/tasks", json={"title": "With due date", "due_date": FUTURE})
    assert response.status_code == 201
    assert response.json()["due_date"] == FUTURE


def test_create_with_invalid_due_date_returns_422(client):
    response = client.post("/tasks", json={"title": "Bad date", "due_date": "not-a-date"})
    assert response.status_code == 422


def test_create_without_due_date_defaults_to_null(client):
    response = client.post("/tasks", json={"title": "No due date"})
    assert response.status_code == 201
    assert response.json()["due_date"] is None


def test_update_due_date_returns_200(client, created_task):
    response = client.patch(f"/tasks/{created_task['id']}", json={"due_date": FUTURE})
    assert response.status_code == 200
    assert response.json()["due_date"] == FUTURE


def test_overdue_filter_returns_only_overdue(client):
    # Overdue: past due date, not Done.
    client.post("/tasks", json={"title": "Overdue task", "due_date": PAST})
    # Not overdue: future due date.
    client.post("/tasks", json={"title": "Future task", "due_date": FUTURE})
    # Not overdue: no due date.
    client.post("/tasks", json={"title": "No date task"})

    response = client.get("/tasks", params={"overdue": "true"})
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["title"] == "Overdue task"


def test_completed_task_is_not_overdue(client):
    # Past due date but already Done -> must NOT be reported as overdue.
    client.post("/tasks", json={"title": "Done past", "due_date": PAST, "status": "Done"})
    response = client.get("/tasks", params={"overdue": "true"})
    assert response.status_code == 200
    assert response.json() == []


def test_overdue_false_returns_non_overdue_only(client):
    client.post("/tasks", json={"title": "Overdue task", "due_date": PAST})
    client.post("/tasks", json={"title": "Future task", "due_date": FUTURE})
    response = client.get("/tasks", params={"overdue": "false"})
    assert response.status_code == 200
    titles = {t["title"] for t in response.json()}
    assert titles == {"Future task"}


# ======================================================================= #
# Feature 2 — Search + combined filters
# ======================================================================= #
def test_search_matches_title(client):
    client.post("/tasks", json={"title": "Write quarterly report"})
    client.post("/tasks", json={"title": "Buy groceries"})
    response = client.get("/tasks", params={"q": "report"})
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["title"] == "Write quarterly report"


def test_search_matches_description(client):
    client.post("/tasks", json={"title": "Task A", "description": "involves the database migration"})
    client.post("/tasks", json={"title": "Task B", "description": "unrelated"})
    response = client.get("/tasks", params={"q": "migration"})
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["title"] == "Task A"


def test_search_is_case_insensitive(client):
    client.post("/tasks", json={"title": "Deploy to Production"})
    response = client.get("/tasks", params={"q": "production"})
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_search_no_match_returns_empty_200(client):
    client.post("/tasks", json={"title": "Something"})
    response = client.get("/tasks", params={"q": "nonexistent"})
    assert response.status_code == 200
    assert response.json() == []


def test_combine_status_and_priority(client):
    client.post("/tasks", json={"title": "A", "status": "InProgress", "priority": "High"})
    client.post("/tasks", json={"title": "B", "status": "InProgress", "priority": "Low"})
    client.post("/tasks", json={"title": "C", "status": "ToDo", "priority": "High"})
    response = client.get("/tasks", params={"status": "InProgress", "priority": "High"})
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["title"] == "A"


def test_combine_search_and_priority(client):
    client.post("/tasks", json={"title": "urgent report", "priority": "High"})
    client.post("/tasks", json={"title": "urgent errand", "priority": "Low"})
    response = client.get("/tasks", params={"q": "urgent", "priority": "High"})
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["title"] == "urgent report"
