# Runbook

Use `docker compose ps` and `docker compose logs --tail=100 backend postgres demo-dependency`. Run `make smoke` to check user CRUD and `make demo-incident` only on the isolated local/demo deployment. Never delete volumes for routine recovery. See docs/incident-response.md.
