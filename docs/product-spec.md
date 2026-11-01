# Product specification

Kinufaktur AI Operations Command Center helps small business operators turn incoming requests into persistent, visible work and gives on-call owners a correlated explanation of workflow failures. Users are operations coordinators, business owners, and engineers responsible for reliability. The application uses synthetic data and needs no paid APIs.

## User journey

An operator creates a task, assigns category and priority, and moves it through the Kanban states. They open Operations overview to inspect live dependency health, request/error/latency metrics, workflow outcomes, alerts, and incident history. They run a workflow; an injected isolated dependency fault causes a real 503. An automatically activated on-call agent inspects structured signals, diagnoses only its supported failure, invokes an allowlisted restoration tool, verifies the dependency through a health check, and records its result. Selecting the incident shows its timestamped timeline and filters its matching traces and structured logs. Task and incident records remain after restart.

## Functional requirements and acceptance

| Requirement | User story | Acceptance evidence |
|---|---|---|
| Persistent task CRUD | As an operator I can create, read, edit, move and delete work | Valid task requests persist; missing IDs return 404; invalid fields return 422; task lifecycle regression tests pass |
| Operations dashboard | As an owner I can inspect business reliability | UI shows health, request count, error rate, average latency, workflow counts and alerts from API; backend outages show an explicit error |
| Workflow execution | As an operator I can run a synthetic business workflow | Healthy dependency yields completion; faulted dependency yields actual failed HTTP response and increments failed workflow metric |
| Correlated telemetry | As an engineer I can follow a user action across signals | Browser sends W3C traceparent and request ID; backend request/database spans and structured logs persist under the matching trace |
| User impact alert | As an on-call owner I am notified of a failed workflow | One actual workflow failure crosses explicit threshold 1, persists a firing alert and associated incident with timestamp and trace |
| Bounded autonomous response | As an on-call owner I can recover a known demo failure safely | Alert activates agent automatically; structured observations support diagnosis; only an allowlisted idempotent demo restoration tool executes; real health verification gates resolution; uncertainty requires human action |
| Incident inspection | As an operator I can review what happened | Incident detail shows diagnosis, action, result, timestamped tool/evidence timeline and correlated telemetry; history persists |
| Demo controls | As a reviewer I can reproduce user impact | Fault injection only works with DEMO_MODE enabled; run workflow exposes failure rather than claiming success; independent evidence script verifies lifecycle |

## API contracts

`GET /docs` provides interactive API documentation. The generated `openapi.json` and running `GET /openapi.json` cover task CRUD and operations routes; the live contract is authoritative.

Task routes: `GET /tasks`, `POST /tasks`, `GET /tasks/{id}`, `PATCH /tasks/{id}`, `DELETE /tasks/{id}`. Task fields include title, description, category, priority and status. Existing Pydantic models define allowed values and field validation.

| Endpoint | Request | Response |
|---|---|---|
| `GET /health` | None | Service health |
| `GET /ops/overview` | None | `health`, request/error/latency/workflow `metrics`, `alerts[]`, `incidents[]` |
| `GET /ops/telemetry` | None | `traces[]` with span hierarchy and duration; structured `logs[]` with correlation IDs |
| `GET /ops/incidents/{id}` | Incident ID | Persisted incident with diagnosis, action, result, status and timeline; 404 for absent ID |
| `POST /ops/demo/fault` | None | Faults only the isolated demo dependency; disabled outside demo mode |
| `POST /workflows/run` | None | 200 completed, or 503 actual dependency failure with incident/trace correlation |

Browser request headers include a fresh W3C `traceparent` and `X-Request-ID` for each action. API errors carry readable `detail` messages. Frontend uses a single request helper and an explicit independent API base URL.

## Persistence and initialization

SQLAlchemy stores business tasks in PostgreSQL in Compose. SQLite supports deterministic local unit/API integration tests. A separate persistent local telemetry database stores spans, sanitized structured events, metrics and incident records so diagnostics are independent of business task storage. Compose volumes preserve state across restarts. Table initialization must fail startup on errors; no silent initialization failure is acceptable. Do not reuse the original submission's database or credentials.

## Non-functional requirements

- Start the complete local stack with `docker compose up --build`; Docker health checks and startup dependencies establish readiness.
- Offline demo must not call paid AI services. Agent decisions use an explicit deterministic policy over structured observations, documented honestly as a bounded agent rather than an LLM.
- Request inputs are validated; telemetry excludes request bodies, SQL values, credentials and sensitive task content.
- On-call has no shell, Docker socket, infrastructure administration or general database tools. Retry budgets and idempotent actions prevent unbounded remediation.
- UI supports narrow screens, keyboard-accessible controls, readable error states and five-second polling; displayed metrics derive from persisted backend observations.
- Unknown failures remain unresolved and require a human; failed verification cannot produce a resolved status.

## Delivery and verification

`make test` runs backend unit/API/database/agent checks, frontend component/request regression tests, and production build; live PostgreSQL integration is part of Compose/CI verification. `make demo-incident` exercises actual services and exports machine-verifiable correlated incident evidence. CI must gate deployment on successful tests, automatically deploy development when configured, and require manual production action. Public deployment, workflow execution and external approvals must be recorded as verified only after actual execution.

The public task tracker and implementation evidence are linked from README and `docs/rubric-evidence.md`. Role definitions and actual contributions are recorded in `docs/agent-team.md` and module implementation notes. The final audit scores only the 12-criterion, 25-point rubric using actual test, runtime and external evidence.
