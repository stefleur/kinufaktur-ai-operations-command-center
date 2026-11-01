.PHONY: test up demo-incident smoke audit
up:
	docker compose up --build

test:
	cd backend && uv sync --locked --group dev && uv run pytest -q
	uv sync --project mcp-server --locked --group dev
	uv run --project mcp-server --locked pytest -q mcp-server/tests agent-hooks/tests
	cd frontend && npm ci && npm run test:ci && npm run build

demo-incident:
	python3 scripts/demo_incident.py --base-url http://localhost:8000 --output evidence/demo-incident.json

smoke:
	python3 scripts/smoke.py

security: audit

audit:
	cd backend && uv export --locked --no-dev --no-hashes --no-emit-project --output-file /tmp/operations-requirements.txt && uv run --with pip-audit pip-audit -r /tmp/operations-requirements.txt
	cd frontend && npm audit --audit-level=high
