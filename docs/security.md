# Security boundaries

This submission uses synthetic task and demonstration data. It has no authentication layer and is intended for a local demonstration or access-controlled evaluation environment. Do not put confidential business data into a publicly exposed instance.

## Runtime on-call agent

The offline agent operates on structured service health, correlated telemetry and workflow-failure evidence. Its only remediation capability resets the isolated synthetic dependency over a fixed HTTP endpoint. It has no shell, subprocess execution, Docker socket, database administration or production infrastructure credentials. Tool calls and outcomes are written to the incident timeline. Execution is bounded; uncertain diagnosis or failed verification leaves an incident requiring human attention rather than claiming recovery. Destructive or production remediation is outside the implemented tool set and requires a separate human-approved implementation.

Fault injection requires `DEMO_MODE=true`; keep it disabled outside synthetic demonstrations. The dependency control token is a local synthetic control boundary, not an authentication scheme for public services. Restrict the dependency to the Compose network. Configure an independent secret if deploying to shared infrastructure; never reuse original-project secrets.

## Data and telemetry

Tasks are validated with Pydantic constraints and enumerated fields; unknown fields and invalid updates are rejected. SQLAlchemy parameterizes data operations. Telemetry must store allowlisted metadata: route templates, operation names, status codes, timing, correlation IDs and safe diagnostic codes. It must exclude bodies, task titles/descriptions, raw SQL parameters, authorization headers, cookies and database connection strings. External correlation headers are untrusted and must be validated before use.

Tasks use PostgreSQL in Compose. Telemetry, alerts and incident history use a separate persistent SQLite file so application database failures need not erase operational evidence. The local telemetry store is single-process: run one backend worker. Configure retention and external authentication before production use; the demonstration intentionally exposes operational views to its local users.

## Repository and deployment

The new repository is an independent tracked-source copy. No original production endpoint, workflow secret, database or provider deployment may be used by default. Environment files, databases, dependency environments and build outputs are excluded from commits. See `docs/source-provenance.json` for attribution.

`make audit` runs the configured dependency audits. Actual results belong in `docs/review.md` and the rubric audit; configuration alone is not a passing scan. Dependency audit findings need review and updates; the project does not claim formal penetration testing or a complete production security assessment.
