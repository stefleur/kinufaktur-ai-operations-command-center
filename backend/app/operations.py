"""Impact alerting and bounded on-call agent with narrow HTTP-only tools."""
import json
import os
import threading
import time
import urllib.error
import urllib.request
from urllib.parse import urlsplit
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

from .observability import request_id_context

class DependencyClient:
    def __init__(self):
        self.base = os.getenv("DEMO_DEPENDENCY_URL", "http://127.0.0.1:9000").rstrip("/")
        parsed = urlsplit(self.base)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment or parsed.path:
            raise ValueError("DEMO_DEPENDENCY_URL must be an HTTP(S) origin without credentials, path, query or fragment.")

    def call(self, path, method="GET"):
        # Paths are static constants in explicit tools. No caller-provided URL or command.
        if path not in {"/health", "/work", "/fault", "/reset"}:
            raise ValueError("Dependency tool path is not allowlisted.")
        request = urllib.request.Request(self.base + path, method=method)
        if path in ("/fault", "/reset"):
            request.add_header("X-Demo-Control", os.getenv("DEMO_CONTROL_TOKEN", "synthetic-local-demo"))
        span = trace.get_current_span().get_span_context()
        if span.is_valid:
            request.add_header("traceparent", f"00-{span.trace_id:032x}-{span.span_id:016x}-01")
        try:
            # Validated HTTP(S) operator origin and static allowlisted paths.
            with urllib.request.urlopen(request, timeout=2) as response:  # nosec B310
                return {"status_code": response.status, **json.load(response)}
        except urllib.error.HTTPError as error:
            return {"status_code": error.code, **json.load(error)}
        except (urllib.error.URLError, TimeoutError, OSError, ValueError):
            return {"status_code": 0, "status": "unavailable"}

    def health(self):
        return self.call("/health")

    def work(self):
        return self.call("/work", "POST")

    def reset(self):
        return self.call("/reset", "POST")

    def fault(self):
        return self.call("/fault", "POST")

class OnCallAgent:
    """Deterministic offline policy agent: observe -> decide -> act -> verify.

    It chooses among reset_demo_dependency and escalate from real observations.
    No LLM claim: the reproducible policy is the offline decision implementation.
    """
    MAX_ACTIONS = 1

    def __init__(self, telemetry, dependency):
        self.telemetry = telemetry
        self.dependency = dependency

    def run(self, incident):
        timeline = incident["timeline"]
        def event(name, **data):
            item = {"timestamp": time.time(), "event": name, **data}
            timeline.append(item)
            self.telemetry.log(name, incident_id=incident["id"], **data)
            self.telemetry.store.add("incident", incident)

        event("agent_activated")
        event("tool_started", tool="inspect_telemetry_and_health")
        health = self.dependency.health()
        logs = [row for row in self.telemetry.store.rows("log") if row["trace_id"] == incident["trace_id"]]
        metrics = self.telemetry.metrics()
        # The currently active span is not yet exported; completed dependency spans are available.
        traces = [row for row in self.telemetry.store.rows("trace") if row["trace_id"] == incident["trace_id"]]
        event("observation", tool="inspect_telemetry_and_health", result={"health": health, "failed_workflow_count": metrics["failed_workflow_count"], "correlated_log_count": len(logs), "correlated_span_count": len(traces)})
        trusted_fault = health["status_code"] == 503 and health.get("status") == "faulted" and any(row["event"] == "workflow_failed" for row in logs)
        demo_enabled = os.getenv("DEMO_MODE", "false").lower() == "true"
        if not trusted_fault or not demo_enabled:
            incident.update(status="needs_human", diagnosis="Dependency cause unknown or automatic demo remediation disabled.", action="escalate", result="No remediation executed.")
            event("human_required", result="Unsafe or uncertain diagnosis; no action allowed.")
            return incident
        incident.update(diagnosis="Isolated demo dependency is deliberately faulted; correlated workflow failure confirms user impact.", action="reset_demo_dependency")
        event("diagnosis", result=incident["diagnosis"])
        # One allowlisted, idempotent action. No retry loop, shell, SQL, or Docker capability.
        event("tool_started", tool="reset_demo_dependency")
        with self.telemetry.tracer.start_as_current_span("agent.reset_demo_dependency", record_exception=False, set_status_on_exception=False):
            action_result = self.dependency.reset()
        event("tool_invocation", tool="reset_demo_dependency", result=action_result)
        event("tool_started", tool="dependency_health")
        with self.telemetry.tracer.start_as_current_span("agent.verify_health", record_exception=False, set_status_on_exception=False):
            recovered = self.dependency.health()
        event("recovery_verification", tool="dependency_health", result=recovered)
        success = action_result["status_code"] == 200 and recovered["status_code"] == 200 and recovered.get("status") == "healthy"
        incident.update(status="resolved" if success else "needs_human", result="Verified dependency recovery through HTTP health check." if success else "Recovery not verified; human intervention required.")
        event("incident_resolved" if success else "human_required", result=incident["result"])
        return incident

def latest(rows):
    records = {}
    for row in rows:
        records.setdefault(row["id"], row)
    return list(records.values())

def operations_router(telemetry, dependency=None):
    router = APIRouter()
    client = dependency or DependencyClient()
    agent = OnCallAgent(telemetry, client)
    incident_lock = threading.Lock()

    @router.get("/health")
    def health():
        from .database import engine
        from sqlalchemy import text
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return {"status": "healthy"}

    @router.get("/ops/overview")
    def overview():
        dep = client.health()
        return {"health": {"status": "healthy" if dep["status_code"] == 200 else "degraded", "dependency": dep}, "metrics": telemetry.metrics(), "incidents": latest(telemetry.store.rows("incident", 1000)), "alerts": latest(telemetry.store.rows("alert", 1000))}

    @router.get("/ops/telemetry")
    def inspection():
        return {"traces": telemetry.store.rows("trace"), "logs": telemetry.store.rows("log")}

    @router.get("/ops/incidents/{incident_id}")
    def incident_details(incident_id: str):
        for incident in latest(telemetry.store.rows("incident", 1000)):
            if incident["id"] == incident_id:
                return incident
        raise HTTPException(404, "Incident not found.")

    @router.post("/ops/demo/fault")
    def fault():
        if os.getenv("DEMO_MODE", "false").lower() != "true":
            raise HTTPException(403, "Fault injection is disabled.")
        result = client.fault()
        telemetry.log("demo_fault_injected", status_code=result["status_code"])
        if result["status_code"] != 200:
            raise HTTPException(503, "Demo dependency control unavailable.")
        return {"status": "faulted"}

    @router.post("/workflows/run")
    def workflow():
        with telemetry.tracer.start_as_current_span("workflow.dependency", record_exception=False, set_status_on_exception=False) as dependency_span:
            result = client.work()
            dependency_span.set_attribute("http.response.status_code", result["status_code"])
            if result["status_code"] != 200:
                dependency_span.set_status(Status(StatusCode.ERROR))
        context = trace.get_current_span().get_span_context()
        trace_id = format(context.trace_id, "032x")
        if result["status_code"] == 200:
            telemetry.store.add("workflow", {"status": "completed", "trace_id": trace_id})
            telemetry.log("workflow_completed")
            return {"status": "completed"}
        telemetry.store.add("workflow", {"status": "failed", "trace_id": trace_id})
        telemetry.log("workflow_failed", status_code=result["status_code"])
        with incident_lock:
            incident = {"id": str(uuid4()), "trace_id": trace_id, "request_id": request_id_context.get(), "status": "open", "diagnosis": "Pending", "action": "none", "result": "Pending", "timeline": [{"timestamp": time.time(), "event": "user_impact_detected"}]}
            telemetry.store.add("incident", incident)
            alert = {"id": str(uuid4()), "incident_id": incident["id"], "trace_id": trace_id, "rule": "workflow_failure", "threshold": 1, "state": "firing"}
            telemetry.store.add("alert", alert)
            telemetry.log("alert_fired", incident_id=incident["id"], rule="workflow_failure")
            try:
                with telemetry.tracer.start_as_current_span("on_call_agent", record_exception=False, set_status_on_exception=False):
                    agent.run(incident)
            except Exception:
                # Unexpected agent/tool faults preserve an unresolved incident; never invent recovery.
                incident.update(status="needs_human", result="Agent execution failed; human intervention required.")
                telemetry.log("agent_failed", incident_id=incident["id"])
            telemetry.store.add("incident", incident)
            alert["state"] = "resolved" if incident["status"] == "resolved" else "firing"
            telemetry.store.add("alert", alert)
        return JSONResponse(status_code=503, content={"detail": "Demo workflow dependency unavailable.", "incident_id": incident["id"], "trace_id": trace_id})

    return router
