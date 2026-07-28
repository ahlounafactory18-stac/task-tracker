"""API tests for the Task Tracker.

Covers create, list (with filters), get-by-id, patch (including status-transition
business rules), and delete. Storage is reset automatically between tests by the
autouse fixture in conftest.py.
"""


# --------------------------------------------------------------------------- #
# Create
# --------------------------------------------------------------------------- #
def test_create_task_returns_201(client):
    response = client.post("/tasks", json={"title": "Write report"})
    assert response.status_code == 201
    body = response.json()
    assert body["id"] == 1
    assert body["title"] == "Write report"


def test_create_missing_title_returns_422(client):
    # Body has no title key at all.
    response = client.post("/tasks", json={})
    assert response.status_code == 422


def test_create_blank_title_returns_422(client):
    # Whitespace-only title must be rejected.
    response = client.post("/tasks", json={"title": "   "})
    assert response.status_code == 422


def test_create_applies_defaults(client):
    response = client.post("/tasks", json={"title": "Default task"})
    body = response.json()
    assert body["status"] == "ToDo"
    assert body["priority"] == "Medium"
    assert body["description"] == ""
    assert body["assignee"] is None


def test_create_rejects_extra_field(client):
    response = client.post("/tasks", json={"title": "ok", "colour": "red"})
    assert response.status_code == 422


# --------------------------------------------------------------------------- #
# List + filters
# --------------------------------------------------------------------------- #
def test_list_empty_returns_200_empty(client):
    response = client.get("/tasks")
    assert response.status_code == 200
    assert response.json() == []


def test_list_returns_all(client):
    client.post("/tasks", json={"title": "A"})
    client.post("/tasks", json={"title": "B"})
    response = client.get("/tasks")
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_list_filter_by_priority(client):
    client.post("/tasks", json={"title": "A", "priority": "High"})
    client.post("/tasks", json={"title": "B", "priority": "Low"})
    response = client.get("/tasks", params={"priority": "High"})
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["priority"] == "High"


def test_list_filter_no_match_returns_empty(client):
    client.post("/tasks", json={"title": "A", "priority": "Low"})
    response = client.get("/tasks", params={"priority": "High"})
    assert response.status_code == 200
    assert response.json() == []


def test_list_invalid_filter_value_returns_422(client):
    response = client.get("/tasks", params={"status": "Archived"})
    assert response.status_code == 422


# --------------------------------------------------------------------------- #
# Get by id
# --------------------------------------------------------------------------- #
def test_get_existing_returns_200(client, created_task):
    response = client.get(f"/tasks/{created_task['id']}")
    assert response.status_code == 200
    assert response.json()["id"] == created_task["id"]


def test_get_missing_returns_404(client):
    response = client.get("/tasks/999")
    assert response.status_code == 404


# --------------------------------------------------------------------------- #
# Patch
# --------------------------------------------------------------------------- #
def test_patch_updates_fields_returns_200(client, created_task):
    response = client.patch(
        f"/tasks/{created_task['id']}", json={"title": "Renamed"}
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Renamed"


def test_patch_missing_returns_404(client):
    response = client.patch("/tasks/999", json={"title": "x"})
    assert response.status_code == 404


def test_patch_invalid_payload_returns_422(client, created_task):
    response = client.patch(
        f"/tasks/{created_task['id']}", json={"status": "Archived"}
    )
    assert response.status_code == 422


def test_patch_missing_id_checked_before_transition(client):
    # Missing id must yield 404, not a 422 from transition validation.
    response = client.patch("/tasks/999", json={"status": "Done"})
    assert response.status_code == 404


# --------------------------------------------------------------------------- #
# Status transitions
# --------------------------------------------------------------------------- #
def test_patch_valid_transition_todo_to_inprogress(client, created_task):
    response = client.patch(
        f"/tasks/{created_task['id']}", json={"status": "InProgress"}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "InProgress"


def test_patch_invalid_transition_todo_to_done(client, created_task):
    response = client.patch(
        f"/tasks/{created_task['id']}", json={"status": "Done"}
    )
    assert response.status_code == 422


def test_patch_same_status_rejected(client, created_task):
    # ToDo -> ToDo is a no-op and must be rejected.
    response = client.patch(
        f"/tasks/{created_task['id']}", json={"status": "ToDo"}
    )
    assert response.status_code == 422


def test_patch_reopen_done_to_inprogress(client, created_task):
    task_id = created_task["id"]
    assert client.patch(f"/tasks/{task_id}", json={"status": "InProgress"}).status_code == 200
    assert client.patch(f"/tasks/{task_id}", json={"status": "Done"}).status_code == 200
    response = client.patch(f"/tasks/{task_id}", json={"status": "InProgress"})
    assert response.status_code == 200
    assert response.json()["status"] == "InProgress"


def test_patch_title_only_skips_transition(client, created_task):
    # A Done task can still be edited by title without a transition error.
    task_id = created_task["id"]
    client.patch(f"/tasks/{task_id}", json={"status": "InProgress"})
    client.patch(f"/tasks/{task_id}", json={"status": "Done"})
    response = client.patch(f"/tasks/{task_id}", json={"title": "Edited while Done"})
    assert response.status_code == 200
    assert response.json()["title"] == "Edited while Done"
    assert response.json()["status"] == "Done"


# --------------------------------------------------------------------------- #
# Delete
# --------------------------------------------------------------------------- #
def test_delete_existing_returns_204_empty_body(client, created_task):
    response = client.delete(f"/tasks/{created_task['id']}")
    assert response.status_code == 204
    assert response.content == b""


def test_delete_missing_returns_404(client):
    response = client.delete("/tasks/999")
    assert response.status_code == 404
