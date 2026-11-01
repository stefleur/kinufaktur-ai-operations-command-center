# Kinufaktur AI Operations Command Center

Small business operators need a reliable view of tasks and workflow execution. This application combines a persistent task board with an operations dashboard so an operator can understand a failed workflow, inspect its trace and see a safe recovery with evidence.

Intended users are operations leads and engineers supporting small business workflows. A failed dependency blocks work; the bounded on-call agent diagnoses the supported isolated fault, resets only that dependency and verifies recovery through HTTP. It uses a deterministic local policy with structured observations and explicit tools. No paid API or LLM is required, and no model reasoning is claimed.

## Run locally

Requirements: Docker Desktop / Docker Engine with Compose. From this repository:

```bash
docker compose up --build
```

Open http://localhost:5173 and http://localhost:8000/docs. Task records live in PostgreSQL; telemetry and incidents live in a separate persistent SQLite volume. All host ports bind to loopback. The included passwords/tokens are synthetic local defaults, not production credentials.

In Task workspace, create a task, edit its status and refresh to see persistence. In Operations, run a workflow, inject a demo fault, then run another workflow. The failed request returns HTTP 503 while the automatically activated agent inspects logs, spans, metrics and dependency health, resets the isolated dependency and records a verified recovery. Inspect the incident timeline and filter telemetry by its trace ID. Run the workflow again to see success.

```bash
make test             # backend + frontend tests and production frontend build
make demo-incident    # against running Compose; asserts full incident lifecycle
python3 scripts/persistence.py  # task/incident persistence across container restarts
make security         # dependency advisory checks
```

`make test` needs Python 3.11+, uv and Node 22+. The full PostgreSQL/container checks run in CI after `make test`. Demo evidence is written to `evidence/demo-incident.json` only after all assertions pass.

## Architecture and evidence

React/Vite → nginx → FastAPI → PostgreSQL tasks. FastAPI also calls an isolated HTTP demo dependency. W3C trace context travels from the browser into OpenTelemetry backend, database and agent spans. A persistent local telemetry exporter supports inspection without a separate paid service. Alerts fire on a real failed workflow and synchronously activate a bounded on-call decision loop.

- [Product specification](docs/product-spec.md), [architecture](docs/architecture.md)
- [Agent team and actual contributions](docs/agent-team.md)
- [Observability](docs/observability.md), [alerting](docs/alerting.md), [incident response](docs/incident-response.md)
- [Testing](docs/testing.md), [security](docs/security.md), [deployment](docs/deployment.md)
- [Evidence and final score](docs/final-rubric-audit.md)
- [Public task tracker](https://github.com/stefleur/kinufaktur-ai-operations-command-center/issues)
- [Actions](https://github.com/stefleur/kinufaktur-ai-operations-command-center/actions)

Public full-stack deployment requires independent infrastructure and deployment hooks. A workflow file alone is not deployment evidence; see the audit for verified status. This is an isolated educational demo with no authentication and must stay private to loopback or behind an authenticated gateway.

Source attribution: derived from the task application in [kinufaktur-ai-chief-of-staff](https://github.com/stefleur/kinufaktur-ai-chief-of-staff), source commit recorded in `docs/source-provenance.json`. No license file was present in the source checkout; no new third-party license grant is asserted. The original repository and its deployment are untouched.
