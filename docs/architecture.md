# Architecture

React keeps the existing task board and adds operations views. Browser HTTP requests generate W3C traceparent plus request IDs. nginx proxies /api to the backend so the deployment can use one origin. FastAPI validates task input; SQLAlchemy persists tasks to PostgreSQL. Initialization creates the schema and fails startup on errors. Future schema changes require migrations before release; create_all is only initial schema creation.

The isolated demo HTTP dependency handles /work, /health, /fault and /reset. Only the backend can reach control endpoints on the Compose network; controls use a synthetic local shared token. The runtime on-call agent has no shell, Docker socket or database administration tool.

OpenTelemetry SDK exports completed spans into a separate SQLite database using a custom persistent exporter. Metadata-only JSON logs, requests and workflow measurements share this store. It stays available during task database failures and persists through container restarts. /ops/telemetry and the React UI inspect it. This deliberately small alternative to Grafana/Tempo provides trace/log correlation and request/workflow metrics. It is designed for one backend process, with unbounded storage growth and aggregate-query cost documented as scale limitations.

On a failed /workflows/run dependency call, the impact rule creates a firing alert and incident. The agent inspects completed dependency spans, matching logs, metrics and real HTTP health, selects one approved reset only for a recognized demo fault, then verifies health and resolves or escalates. A synchronous lock serializes incident actions within this process. It does not provide distributed deduplication; use one backend worker.
