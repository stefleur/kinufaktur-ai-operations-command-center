# Reproducible testing

Run `make test` from the repository root. The command runs deterministic backend unit/API/database/agent tests and React unit tests plus the production frontend build. No paid APIs or model keys are needed. The on-call policy is deterministic and tests use controlled dependency responses; live recovery is independently checked by the demonstration below.

## Live system demonstration

1. Start the full local stack: `docker compose up --build`.
2. Run `make demo-incident` in another terminal.
3. Inspect the dashboard and `evidence/demo-incident.json`.

The evidence collector in `scripts/demo_incident.py` makes real HTTP requests. It checks a successful baseline workflow, injects an isolated dependency fault, requires a failing workflow HTTP 503, verifies trace propagation from its W3C `traceparent`, and checks the stored incident, timestamped timeline, tool invocation, resolved alert, failed-workflow metric, OpenTelemetry spans and structured logs. It then requires healthy HTTP responses and a successful recovered workflow. Any failed assertion exits nonzero; no evidence file is written as a successful run until every check passes.

The collector can target another independently deployed demo:

```bash
python3 scripts/demo_incident.py --base-url http://localhost:8000 --output evidence/demo-incident.json
```

Fault injection must be explicitly enabled using `DEMO_MODE=true`. Run only against synthetic evaluation deployments.

## Persistence

Use the PostgreSQL integration test and container restart check documented in the final rubric audit. SQLite-backed API tests are useful deterministic checks but do not establish PostgreSQL behavior or persistence across Docker restarts. Runtime evidence must identify which database and services actually ran. Named volumes persist after `docker compose stop`/`start` or service restarts; do not use `down --volumes` when testing persistence.

## Evidence labels

Distinguish implemented test code, local test execution, CI execution and public deployment verification. A successful frontend build does not establish browser-level interaction. A workflow YAML does not establish a successful workflow run. Historical source-project audits do not establish verification of this repository. Exact executed commands, results and remaining limitations are recorded in `docs/review.md` and `docs/final-rubric-audit.md`.
