# Agent Extension Pack

The Kinufaktur AI Operations Command Center development extension pack supplies bounded task API context and review tools. Runtime incident response is implemented separately in `backend/app/operations.py`.

- `AGENTS.md` provides the existing project-wide instructions and boundaries.
- `agent-capabilities/task-api-change.md` defines the spec -> bounded implementation -> tests -> specialist review -> human approval workflow.
- `custom-agent/api-test-reviewer.md` is a read-only API and test review specialist.
- `mcp-server/server.py` exposes one read-only MCP tool for the fixed specification, API contract, or project instructions.
- `agent-hooks/check_protected_files.py` checks staged paths for obvious secret and credential filenames.
- `docs/permissions.md` records access boundaries and limitations.

## MCP setup and smoke test

From the repository root:

```bash
uv sync --project mcp-server --locked --group dev
uv run --project mcp-server --locked pytest -q mcp-server/tests agent-hooks/tests
```

Configure an MCP client to launch `uv run --project <repository>/mcp-server --locked python <repository>/mcp-server/server.py` over stdio. The server exposes only `get_project_context(section)`; see `docs/permissions.md` for its fixed sections and file mapping.

Run the staged-path guardrail from the repository root:

```bash
python3 agent-hooks/check_protected_files.py
```

The guardrail is advisory filename screening, not secret detection or a substitute for repository and platform controls.

These development role files describe reproducible specialist instructions; actual delegated contributions are recorded in `docs/agent-team.md`. They do not install a Codex agent automatically. The MCP remains a read-only documentation server with no runtime remediation authority.

## Relocation verification

During the independent-project implementation, the delegated Backend Engineering agent updated the MCP fixed paths to `docs/product-spec.md`, `openapi.json`, and `AGENTS.md`, renamed its package/server identity, and corrected the staged-file hook's repository root. Added a regression check that the hook cannot accidentally inspect the parent workspace. Updated development role instructions and patched the inherited MCP `certifi` dependency to 2026.10.23.

Actual check on 2026-11-01: `mcp-server/.venv/bin/python -m pytest -q mcp-server/tests agent-hooks/tests` — **12 passed in 2.33s**. This includes real stdio MCP protocol initialization and fixed-section reads, invalid section rejection, external symlink rejection, and staged-path guardrail behavior.
