# Development workflow

Read AGENTS.md and the product contract, then choose the relevant backend, frontend, SRE or review context. Keep unrelated history out of each agent context. Preserve original task tests and metadata-only telemetry. Role handoffs and review gates are in agent-team.md.

Use a branch and pull request for changes after the initial independent import. `make test` is required before merging; CI also starts the actual Compose PostgreSQL stack, checks CRUD, demonstrates remediation and restarts containers to verify persistence. Failed tests fail the test job and block downstream deployment.

Record actual commands/results and update the final audit. Public issues contain acceptance criteria, implementation status, commits, test evidence and actual agent contributions. Do not confuse a configured workflow with executed deployment proof.
