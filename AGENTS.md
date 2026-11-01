# Kinufaktur AI Operations Command Center
Read docs/product-spec.md and docs/architecture.md for context. Consult only the module needed for your task.

Preserve task CRUD. Use synthetic data only. Never read production credentials or modify the source repository. User authorized implementation, commits, new public repository, CI and deployment to independently available infrastructure. Never reuse original infrastructure or secrets.

Backend: FastAPI/SQLAlchemy. Frontend: React/Vite. OpenTelemetry traces and structured logs must exclude request bodies and secrets. On-call tools must remain allowlisted, bounded and restricted to the isolated demo dependency. No shell or infrastructure tools in the runtime agent.

Run make test and make demo-incident. Record actual results in docs; do not claim unexecuted checks. See docs/agent-team.md, docs/testing.md, docs/security.md, docs/deployment.md and docs/final-rubric-audit.md. Initialization failures must fail startup.
