#!/usr/bin/env python3
"""Exercise live HTTP endpoints and persist independently checked incident evidence."""
import argparse
import json
import secrets
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def request(base, path, method="GET", trace_id=None):
    headers = {"Accept": "application/json"}
    if trace_id:
        headers["traceparent"] = f"00-{trace_id}-{secrets.token_hex(8)}-01"
        headers["X-Request-ID"] = f"demo-{secrets.token_hex(12)}"
    req = Request(base.rstrip("/") + path, method=method, headers=headers)
    try:
        response = urlopen(req, timeout=15)
    except HTTPError as error:
        response = error
    with response:
        return {"status": response.status, "headers": dict(response.headers),
                "body": json.loads(response.read().decode())}


def run(base, output):
    evidence = {"recorded_at": datetime.now(timezone.utc).isoformat(), "base_url": base}
    evidence["baseline"] = request(base, "/workflows/run", "POST")
    require(evidence["baseline"]["status"] == 200, "Baseline workflow must complete before fault injection")
    evidence["fault"] = request(base, "/ops/demo/fault", "POST")
    require(evidence["fault"]["status"] == 200, "Fault injection denied; start local stack with DEMO_MODE=true")
    trace_id = secrets.token_hex(16)
    evidence["failed_request"] = request(base, "/workflows/run", "POST", trace_id)
    require(evidence["failed_request"]["status"] == 503, "Fault must cause an actual user workflow HTTP 503")
    failure = evidence["failed_request"]["body"]
    require(failure.get("trace_id") == trace_id, "W3C traceparent must propagate to failed workflow")
    incident_id = failure.get("incident_id")
    require(incident_id, "User-impacting failure did not create an incident")
    deadline = time.monotonic() + 30
    while True:
        incident_response = request(base, f"/ops/incidents/{incident_id}")
        require(incident_response["status"] == 200, "Incident history endpoint failed")
        incident = incident_response["body"]
        if incident.get("status") == "resolved":
            break
        require(time.monotonic() < deadline, f"Recovery not verified within deadline: {incident.get('status')}")
        time.sleep(0.2)
    require(incident.get("trace_id") == trace_id, "Incident not correlated with failed request")
    require(incident.get("diagnosis") and incident.get("action") and incident.get("result"), "Incident must persist diagnosis, action and result")
    timeline = incident.get("timeline", [])
    require(len(timeline) >= 4 and all(event.get("timestamp") for event in timeline), "Incomplete timestamped incident timeline")
    require(any(event.get("event") == "agent_activated" for event in timeline), "Alert did not activate agent")
    require(any(event.get("event") == "observation" for event in timeline), "No structured agent observation")
    require(any(event.get("tool") == "reset_demo_dependency" and event.get("result", {}).get("status_code") == 200 for event in timeline if isinstance(event.get("result"), dict)), "No successful allowlisted remediation tool call")
    require(any(event.get("event") == "recovery_verification" and event.get("result", {}).get("status_code") == 200 for event in timeline if isinstance(event.get("result"), dict)), "No actual successful dependency health verification")
    evidence["incident"] = incident
    overview = request(base, "/ops/overview")
    require(overview["status"] == 200, "Operations overview failed")
    evidence["overview"] = overview["body"]
    alerts = [a for a in overview["body"].get("alerts", []) if a.get("incident_id") == incident_id]
    require(alerts and all(a.get("trace_id") == trace_id and a.get("state") == "resolved" for a in alerts), "No resolved trace-correlated alert")
    require(overview["body"]["metrics"]["failed_workflow_count"] >= 1, "Actual failed workflow absent from metrics")
    telemetry = request(base, "/ops/telemetry")
    require(telemetry["status"] == 200, "Telemetry inspection failed")
    evidence["correlated_telemetry"] = {kind: [row for row in telemetry["body"].get(kind, []) if row.get("trace_id") == trace_id] for kind in ("traces", "logs")}
    require(evidence["correlated_telemetry"]["traces"], "No persisted OpenTelemetry spans for failed request")
    logs = evidence["correlated_telemetry"]["logs"]
    require(logs and any(row.get("request_id") for row in logs), "No request-correlated structured logs")
    require(any(row.get("event") == "workflow_failed" for row in logs), "Missing structured user-impact error log")
    require(any(row.get("event") == "alert_fired" for row in logs), "Missing structured automatic alert event")
    evidence["health"] = request(base, "/health")
    require(evidence["health"]["status"] == 200, "Live health check failed after remediation")
    evidence["recovered_request"] = request(base, "/workflows/run", "POST")
    require(evidence["recovered_request"]["status"] == 200, "User workflow did not recover after remediation")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(evidence, indent=2) + "\n")
    print(f"Verified live incident {incident_id}; trace {trace_id}; evidence: {output}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--output", type=Path, default=Path("evidence/demo-incident.json"))
    args = parser.parse_args()
    try:
        run(args.base_url, args.output)
    except (RuntimeError, URLError, KeyError, ValueError) as error:
        print(f"Incident demonstration failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
