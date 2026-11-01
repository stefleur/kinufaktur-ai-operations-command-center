# Independent QA and security review

Reviewer: actual delegated Codex agent `/root/qa_security`, serving the QA/Testing and Security/Review responsibilities during this implementation. This is automated technical review, not a claim of human approval or independent organizational certification.

## Executed checks

On 2026-11-01, in the new repository's `backend/`, `uv run pytest -q` passed **20 tests in 3.44 seconds**. Two dependency deprecation warnings concerned FastAPI/Starlette `httpx` TestClient and the anyio BlockingPortal alias; no failures were ignored. The suite includes original task regressions, real SQLAlchemy persistence lifecycle tests, real local HTTP dependency fault/recovery, trace correlation, alert generation, safe escalation, failed remediation and telemetry redaction checks. This execution used the local Python 3.13 virtual environment. It does not establish Docker/PostgreSQL deployment by itself.

`python3 -m py_compile scripts/demo_incident.py` passed. The collector requires observed runtime evidence and exits nonzero on missing evidence. Live-system execution results are recorded below or in `docs/final-rubric-audit.md` once actually run.

## Findings and corrections

- **Persistent incident snapshots:** review caught reuse of entity IDs as SQLite event primary keys, which would break repeated incident/alert updates. Backend corrected storage row IDs to fresh UUIDs while preserving stable entity IDs inside snapshot JSON.
- **Database initialization:** inherited code swallowed schema-creation failures. Backend now allows initialization failure to stop startup.
- **Telemetry privacy:** middleware stores route templates, not arbitrary request paths or query strings. Backend tests verify sensitive payload and unknown-path strings are absent from inspected telemetry. SQL operation visibility excludes statement parameters.
- **Agent evidence:** review requested recording tool invocation before executing the reset so unexpected exceptions do not erase invocation intent. Backend added `tool_started` events; successful results and independent health verification are separately recorded.
- **External-service isolation:** frontend review identified the inherited original-production fallback URL. Frontend agent removed it. Only independently configured backend or local defaults are used.
- **Dependency audit accuracy:** review identified a Makefile audit path hardcoded to Python 3.11 while the local environment uses 3.13; reported to DevOps for correction. Audit results must identify actual inspected packages.

## Runtime safety assessment

The implemented agent observes structured health plus correlated workflow telemetry, chooses a single allowlisted reset only for the known isolated synthetic fault, verifies a fresh HTTP health check, and escalates unknown causes or failed recovery. Inspection confirmed no runtime shell, Docker, arbitrary SQL or production infrastructure tool. One straight-line reset action bounds remediation; HTTP requests have timeouts. Demo control is disabled unless explicitly enabled. The policy is deterministic and does not claim LLM execution.

## Remaining limits

The application has no authentication or per-user authorization and stores unbounded local telemetry; keep public demonstrations synthetic and access controlled. This review does not establish penetration-test coverage, dependency vulnerability clearance, public deployment, CI success or human approval unless supported by separately recorded evidence. Historical source-project scan files and audit text are not evidence for the new repository.

## Verified live incident demonstration

`make demo-incident` passed on 2026-11-01 against the actual local Docker Compose services at `http://localhost:8000`. Evidence: [`evidence/demo-incident.json`](../evidence/demo-incident.json).

- Incident: `5efd4c49-c870-4f44-b0c7-d3d13aa28935`.
- W3C trace: `024e53116b7509fe8a534f267c911e14`.
- Baseline workflow HTTP 200; fault-induced workflow HTTP 503; recovered workflow HTTP 200; live health HTTP 200.
- Five persisted correlated OpenTelemetry spans and twelve correlated structured log events.
- Actual automatic alert, ten timestamped timeline events, pre-execution tool recording, allowlisted reset HTTP success, distinct dependency health verification, and resolved incident/alert.

The collector verified every condition from runtime responses; it did not insert incident, alert, trace or recovery records. The first sandboxed attempt could not access localhost; the authorized rerun succeeded. This local result establishes no public deployment claim.

## Dependency and static scans

Initial `make security` correctly failed for locked `certifi==2026.7.22` (PYSEC-2026-4320) and `dnspython==2.8.0` (CVE-2026-114605). Backend upgraded to `certifi==2026.10.23` and `dnspython==2.9.1`; the final audit rerun is recorded below when complete.

Initial `npm audit --audit-level=high` reported five development-tooling vulnerabilities, including critical tinypool issues through old Vitest and high Vite/source-map-js issues. Frontend agent is updating these dependencies; initial failures are retained here as findings, not passing evidence.

`gitleaks dir backend/app --no-banner --redact`, equivalent scans of `frontend/src` and `scripts`, each reported **no leaks found**. This is a scoped source scan, not proof that every dependency or historical file contains no secret.

Initial `bandit -r backend/app -q` found two medium issues: private Compose service binding on all interfaces, and urllib scheme validation. Backend added strict HTTP(S) origin and fixed-path validation plus six safety tests; narrow `B104` and `B310` annotations document the intentional private bind and validated HTTP client. The follow-up Bandit execution exited zero with no unsuppressed findings. These accepted annotations are explicitly disclosed rather than represented as absent risk.

Frontend agent final checks after upgrades: npm audit reports zero vulnerabilities; 13 tests and build passed. Backend checks passed 27 tests; MCP/hook checks passed 12 tests. Root PostgreSQL container restart check passed, preserving both task and incident IDs. Browser screenshot execution was rejected by the tool approval boundary, so no screenshot or browser E2E is claimed. Root make test encountered a sandbox uv-cache access error; individual agent executions above passed and full CI is pending.
