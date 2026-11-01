from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import create_app


TASK_INPUT = {
    "title": "Automate invoice intake",
    "description": "Map the current invoice workflow.",
    "category": "AI Automation",
    "priority": "High",
    "status": "incoming",
}


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    test_session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        with test_session() as session:
            yield session

    test_app = create_app(initialize_database=False)
    test_app.dependency_overrides[get_db] = override_get_db

    with TestClient(test_app) as test_client:
        yield test_client

    Base.metadata.drop_all(bind=engine)
    engine.dispose()


def create_task(client, **changes):
    payload = {**TASK_INPUT, **changes}
    response = client.post("/tasks", json=payload)
    assert response.status_code == 201
    return response.json()


def test_list_tasks_starts_with_isolated_empty_database(client):
    response = client.get("/tasks")

    assert response.status_code == 200
    assert response.json() == []


def test_list_tasks_returns_all_tasks(client):
    first = create_task(client)
    second = create_task(client, title="Consolidate customer data", category="Data")

    response = client.get("/tasks")

    assert response.status_code == 200
    assert {task["id"] for task in response.json()} == {first["id"], second["id"]}


def test_get_task_returns_one_task(client):
    task = create_task(client)

    response = client.get(f"/tasks/{task['id']}")

    assert response.status_code == 200
    assert response.json() == task


def test_get_unknown_task_returns_404(client):
    response = client.get("/tasks/missing-task")

    assert response.status_code == 404
    assert response.json() == {"detail": "Task not found."}


def test_create_task_returns_complete_task(client):
    response = client.post("/tasks", json=TASK_INPUT)

    assert response.status_code == 201
    task = response.json()
    assert isinstance(task["id"], str)
    assert task["id"]
    assert {field: task[field] for field in TASK_INPUT} == TASK_INPUT
    assert datetime.fromisoformat(task["created_at"])
    assert datetime.fromisoformat(task["updated_at"])


def test_create_task_rejects_invalid_data(client):
    response = client.post(
        "/tasks",
        json={**TASK_INPUT, "priority": "Urgent", "unexpected": True},
    )

    assert response.status_code == 422
    assert response.json() == {"detail": "Invalid task data."}


def test_patch_task_updates_only_supplied_fields(client):
    task = create_task(client)

    response = client.patch(
        f"/tasks/{task['id']}",
        json={"status": "in_progress"},
    )

    assert response.status_code == 200
    updated_task = response.json()
    assert updated_task["status"] == "in_progress"
    assert updated_task["title"] == task["title"]
    assert updated_task["created_at"] == task["created_at"]


def test_patch_task_rejects_empty_body(client):
    task = create_task(client)

    response = client.patch(f"/tasks/{task['id']}", json={})

    assert response.status_code == 422
    assert response.json() == {"detail": "Invalid task data."}


def test_patch_unknown_task_returns_404(client):
    response = client.patch("/tasks/missing-task", json={"status": "done"})

    assert response.status_code == 404
    assert response.json() == {"detail": "Task not found."}


def test_delete_task_removes_and_returns_its_id(client):
    task = create_task(client)

    response = client.delete(f"/tasks/{task['id']}")

    assert response.status_code == 200
    assert response.json() == {"id": task["id"]}
    assert client.get(f"/tasks/{task['id']}").status_code == 404


def test_delete_unknown_task_returns_404(client):
    response = client.delete("/tasks/missing-task")

    assert response.status_code == 404
    assert response.json() == {"detail": "Task not found."}


def test_cors_allows_frontend_development_origin(client):
    response = client.options(
        "/tasks",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
