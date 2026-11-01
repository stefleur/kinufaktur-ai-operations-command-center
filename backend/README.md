# Operations backend

FastAPI/SQLAlchemy tasks and OpenTelemetry-backed operations APIs. Root README provides Docker setup; `make test` runs all checks.

Local source run: `uv sync --locked --group dev`, then `uv run uvicorn app.main:app --port 8000`. Run the synthetic dependency separately using `uv run python -m app.demo_dependency`; set `DEMO_MODE=true` on the API to enable fault injection/remediation. Default dependency URL is loopback port 9000. No external API required.

`DATABASE_URL` configures task persistence (SQLite locally, PostgreSQL in Compose); `TELEMETRY_DB` configures the independent persistent SQLite telemetry store. `DEMO_DEPENDENCY_URL` is operator configuration, never user input. `DEMO_CONTROL_TOKEN` controls isolated dependency state and is never logged.

API contracts are generated at `/openapi.json`; interactive documentation is `/docs`. New endpoints: `GET /health`, `GET /ops/overview`, `GET /ops/telemetry`, `GET /ops/incidents/{id}`, `POST /ops/demo/fault`, `POST /workflows/run`.

Failure threshold: one failed real workflow dependency request creates an alert and incident and immediately activates the bounded on-call agent. It observes correlated logs/traces, workflow metrics and live dependency health, decides between reset and human escalation, executes at most one idempotent reset, and verifies recovery through a separate HTTP health request. This is a deterministic offline policy agent; no LLM is claimed. Failed user requests remain HTTP 503 even after recovery, so callers know to retry. Telemetry/incident SQLite persists independently of task database outages.

OpenTelemetry SDK spans are exported synchronously to SQLite; the operations UI is the local telemetry inspection backend. SQL spans contain only operation categories. Request logs contain route templates, trace/request IDs, status and latency. Request bodies, SQL text/parameters, headers and arbitrary URLs are excluded.
