# Agent team and actual execution

This implementation used supported Codex delegation on 2026-11-01. Six responsibilities were assigned across four executing agents; six separate processes are not claimed.

| Role | Executing agent | Inputs | Outputs / allowed tools |
|---|---|---|---|
| Product/Specification | frontend | user brief, source app, API contract | docs/product-spec.md; repository reads and scoped writes |
| Backend Engineering | backend | source CRUD, agreed HTTP contract | backend implementation/tests; shell, uv, Python |
| Frontend Engineering | frontend | operations API, product requirements | React dashboard/tests; shell, npm |
| DevOps/SRE | root | source provenance, runtime and CI requirements | isolated copy, Compose, CI, repository/environments, evidence; git, gh, Docker |
| QA/Testing | qa_security | API contract and runtime | HTTP incident collector, independent test execution, review; Python, uv, Docker |
| Security/Review | qa_security | runtime agent and telemetry code | docs/security.md and docs/review.md; read/review code, advisory checks |

Handoffs: backend supplied routes and dependency port/environment contract to frontend, QA and SRE. Frontend tested its component and HTTP integration. QA checked incident assertions and agent safety, requested pre-action tool records, and identified copied historical evidence and audit-path errors. Backend and root corrected these before delivery. Actual implementation records are backend/IMPLEMENTATION.md, frontend/IMPLEMENTATION.md and docs/review.md. No earlier source-project agent history is represented as this work.

Review gates: retain task regressions, pass module tests, run the real HTTP demo, verify PostgreSQL restart persistence, audit dependencies and inspect final evidence. Root owns integration conflicts and updates the contract before incompatible changes. QA reports failures directly to the owning agent. Human review remains distinct from automated review.

User authorization covered creating/pushing this new public repository and independently available deployments. Original infrastructure is out of scope. Production/destructive runtime actions require a human and have no implementation in the on-call agent. The runtime on-call agent is separate from development agents and exposes only explicit safe tools.

Context management: read root AGENTS.md, then only the relevant module docs. Pass the short API/environment contract between roles; link evidence paths rather than pasting entire logs. Ask an owner before editing another role's module. Repository tracker issues record role contributions, acceptance criteria, test evidence and associated commits.
