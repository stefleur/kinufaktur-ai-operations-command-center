import pytest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import database
from app.database import Base
from app.main import create_app


TASK_INPUT = {
    "title": "Automate invoice intake",
    "description": "Map the current invoice workflow.",
    "category": "AI Automation",
    "priority": "High",
    "status": "incoming",
}


def create_task(client, **changes):
    payload = {**TASK_INPUT, **changes}
    response = client.post("/tasks", json=payload)
    assert response.status_code == 201
    return response.json()


@pytest.fixture
def integration_client(monkeypatch):
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    try:
        monkeypatch.setattr(database, "engine", engine)
        monkeypatch.setattr(
            database,
            "SessionLocal",
            sessionmaker(bind=engine, autoflush=False, expire_on_commit=False),
        )
        with TestClient(create_app(initialize_database=True)) as client:
            yield client
    finally:
        try:
            Base.metadata.drop_all(bind=engine)
        finally:
            engine.dispose()


@pytest.mark.integration
def test_full_task_lifecycle_uses_real_persistence(integration_client):
    client = integration_client
    # Create
    task = create_task(client)
    task_id = task["id"]

    # List
    resp = client.get("/tasks")
    assert resp.status_code == 200
    assert any(t["id"] == task_id for t in resp.json())

    # Get
    resp = client.get(f"/tasks/{task_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == task_id

    # Update (title)
    resp = client.patch(f"/tasks/{task_id}", json={"title": "New title"})
    assert resp.status_code == 200
    updated = resp.json()
    assert updated["title"] == "New title"
    assert updated["created_at"] == task["created_at"]

    # Change status
    resp = client.patch(f"/tasks/{task_id}", json={"status": "in_progress"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "in_progress"

    # Delete
    resp = client.delete(f"/tasks/{task_id}")
    assert resp.status_code == 200
    assert resp.json() == {"id": task_id}

    # Verify persistence (deleted)
    assert client.get(f"/tasks/{task_id}").status_code == 404


@pytest.mark.integration
def test_restart_persistence_and_database_span_correlation(tmp_path, monkeypatch):
    """A fresh application and engine read a previously committed task."""
    from app.observability import Observability
    db_url = "sqlite:///" + str(tmp_path / "persistent-tasks.db")
    telemetry_path = str(tmp_path / "persistent-telemetry.db")
    trace_id = "fedcba0987654321fedcba0987654321"
    task_id = None
    for restart in range(2):
        engine = create_engine(db_url, connect_args={"check_same_thread": False})
        monkeypatch.setattr(database, "engine", engine)
        monkeypatch.setattr(database, "SessionLocal", sessionmaker(bind=engine, autoflush=False, expire_on_commit=False))
        with TestClient(create_app(telemetry_path=telemetry_path)) as client:
            if restart == 0:
                response = client.post("/tasks", json=TASK_INPUT, headers={"traceparent": f"00-{trace_id}-0123456789abcdef-01"})
                assert response.status_code == 201
                task_id = response.json()["id"]
                telemetry = client.get("/ops/telemetry").json()
                spans = [s for s in telemetry["traces"] if s["trace_id"] == trace_id]
                assert any(s["name"] == "database.INSERT" for s in spans)
                assert any(s["name"] == "POST /tasks" for s in spans)
                assert all("statement" not in str(s["attributes"]) for s in spans)
            else:
                response = client.get("/tasks/" + task_id)
                assert response.status_code == 200
                assert response.json()["title"] == TASK_INPUT["title"]
        engine.dispose()
    reader = Observability(telemetry_path)
    assert any(s["name"] == "database.INSERT" for s in reader.store.rows("trace"))
    reader.provider.shutdown()
    reader.store.close()
