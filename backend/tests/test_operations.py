"""Real HTTP dependency, OpenTelemetry, persistence and bounded remediation tests."""
import threading

import pytest
from fastapi.testclient import TestClient
from http.server import ThreadingHTTPServer

from app import demo_dependency
from app.main import create_app
from app.observability import Observability
from app.operations import OnCallAgent


@pytest.fixture
def operations(tmp_path, monkeypatch):
    monkeypatch.setenv("DEMO_MODE", "true")
    monkeypatch.setenv("DEMO_CONTROL_TOKEN", "test-isolated-token")
    demo_dependency.faulted = False
    server = ThreadingHTTPServer(("127.0.0.1", 0), demo_dependency.Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    monkeypatch.setenv("DEMO_DEPENDENCY_URL", f"http://127.0.0.1:{server.server_port}")
    path = str(tmp_path / "telemetry.db")
    app = create_app(initialize_database=False, telemetry_path=path)
    with TestClient(app) as client:
        yield client, path
    server.shutdown()
    server.server_close()
    thread.join(timeout=3)


def test_end_to_end_failure_correlates_and_agent_verifies_real_recovery(operations):
    client, path = operations
    assert client.post("/workflows/run").json() == {"status": "completed"}
    assert client.post("/ops/demo/fault").status_code == 200
    trace_id = "1234567890abcdef1234567890abcdef"
    response = client.post("/workflows/run", headers={"traceparent": f"00-{trace_id}-1234567890abcdef-01", "x-request-id": "journey-test"})
    assert response.status_code == 503
    assert response.json()["trace_id"] == trace_id
    incident = client.get("/ops/incidents/" + response.json()["incident_id"]).json()
    assert incident["status"] == "resolved"
    assert incident["action"] == "reset_demo_dependency"
    assert incident["request_id"] == "journey-test"
    timeline = incident["timeline"]
    assert [r["event"] for r in timeline if r["event"] != "tool_started"] == ["user_impact_detected", "agent_activated", "observation", "diagnosis", "tool_invocation", "recovery_verification", "incident_resolved"]
    assert timeline[-2]["result"]["status_code"] == 200
    observation = next(row["result"] for row in timeline if row["event"] == "observation")
    assert observation["correlated_log_count"] >= 1
    assert observation["correlated_span_count"] >= 1
    assert len([r for r in timeline if r["event"] == "tool_invocation"]) == 1
    overview = client.get("/ops/overview").json()
    assert overview["health"]["status"] == "healthy"
    assert overview["metrics"]["failed_workflow_count"] == 1
    assert overview["metrics"]["error_count"] == 1
    assert overview["alerts"][0]["state"] == "resolved"
    evidence = client.get("/ops/telemetry").json()
    assert any(s["trace_id"] == trace_id and s["name"] == "POST /workflows/run" and s["status"] == "ERROR" for s in evidence["traces"])
    assert any(s["trace_id"] == trace_id and s["name"] == "agent.verify_health" for s in evidence["traces"])
    assert any(r["trace_id"] == trace_id and r["event"] == "workflow_failed" for r in evidence["logs"])
    assert client.post("/workflows/run").status_code == 200
    # A second independent reader can inspect the persisted incident.
    reader = Observability(path)
    assert any(row["status"] == "resolved" for row in reader.store.rows("incident"))
    reader.provider.shutdown()
    reader.store.close()


def test_fault_injection_requires_explicit_demo_mode(operations, monkeypatch):
    client, _ = operations
    monkeypatch.setenv("DEMO_MODE", "false")
    assert client.post("/ops/demo/fault").status_code == 403


def test_dependency_control_rejects_wrong_token(operations, monkeypatch):
    client, _ = operations
    # Server and client use same env; direct HTTP deliberately sends wrong token.
    import urllib.request
    import urllib.error
    import os
    req = urllib.request.Request(os.environ["DEMO_DEPENDENCY_URL"] + "/fault", method="POST", headers={"X-Demo-Control": "wrong"})
    with pytest.raises(urllib.error.HTTPError) as error:
        urllib.request.urlopen(req)
    assert error.value.code == 403
    assert client.post("/workflows/run").status_code == 200


def test_uncertain_diagnosis_escalates_without_action(tmp_path, monkeypatch):
    monkeypatch.setenv("DEMO_MODE", "true")
    class UnknownDependency:
        resets = 0
        def health(self):
            return {"status_code": 0, "status": "unavailable"}
        def reset(self):
            self.resets += 1
    telemetry = Observability(str(tmp_path / "agent.db"))
    dep = UnknownDependency()
    incident = {"id": "unknown", "trace_id": "0"*32, "timeline": []}
    result = OnCallAgent(telemetry, dep).run(incident)
    assert result["status"] == "needs_human"
    assert dep.resets == 0
    telemetry.provider.shutdown()
    telemetry.store.close()


def test_failed_remediation_does_not_claim_recovery(tmp_path, monkeypatch):
    monkeypatch.setenv("DEMO_MODE", "true")
    class BrokenReset:
        resets = 0
        def health(self):
            return {"status_code": 503, "status": "faulted"}
        def reset(self):
            self.resets += 1
            return {"status_code": 503, "status": "faulted"}
    telemetry = Observability(str(tmp_path / "agent.db"))
    telemetry.log("workflow_failed")
    dep = BrokenReset()
    incident = {"id": "broken", "trace_id": "0"*32, "timeline": []}
    result = OnCallAgent(telemetry, dep).run(incident)
    assert result["status"] == "needs_human"
    assert dep.resets == 1
    assert result["timeline"][-1]["event"] == "human_required"
    telemetry.provider.shutdown()
    telemetry.store.close()


def test_payloads_and_unknown_paths_are_not_stored(operations):
    client, _ = operations
    secret = "sensitive-should-never-appear"
    client.post("/tasks", json={"secret": secret})
    client.get("/unknown/" + secret + "?token=" + secret)
    evidence = client.get("/ops/telemetry").text
    assert secret not in evidence
    assert "unmatched" in evidence


def test_invalid_request_id_is_replaced(operations):
    client, _ = operations
    response = client.get("/ops/telemetry", headers={"x-request-id": "unsafe content"})
    assert response.headers["x-request-id"] != "unsafe content"


@pytest.mark.parametrize("origin", ["file:///tmp/foo", "http://user:pass@localhost:9000", "http://localhost:9000/path", "http://localhost:9000?secret=value", "http://localhost:9000#fragment"])
def test_dependency_origin_rejects_non_http_and_unsafe_configuration(monkeypatch, origin):
    from app.operations import DependencyClient
    monkeypatch.setenv("DEMO_DEPENDENCY_URL", origin)
    with pytest.raises(ValueError):
        DependencyClient()


def test_dependency_tool_rejects_unapproved_path():
    from app.operations import DependencyClient
    with pytest.raises(ValueError):
        DependencyClient().call("/admin")
