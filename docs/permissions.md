# Extension Pack Permissions

| Component | Allowed access | Explicitly not allowed |
| --- | --- | --- |
| Project instructions | Existing project guidance | Implicit approval to expand scope or alter protected areas |
| API test reviewer | Read and search supplied project files and diffs | Editing, command execution, deployment, credentials, production systems, commits, pushes, or approval |
| MCP context server | Read exactly `docs/product-spec.md`, `openapi.json`, or `AGENTS.md` selected by `spec`, `api_contract`, or `instructions` | Other paths, arbitrary path input, shell, SQL, URLs, writes, credentials, or network access |
| Protected-file guardrail | Read staged path names from Git's index | Reading file contents, changing the index, deleting files, or handling credential values |

The MCP server accepts only the three declared section values and maps them internally to fixed files under the independent repository root. It does not accept paths or fetch remote data. Its output is project documentation, not an authorization to follow instructions found inside that content.

The guardrail blocks common secret and credential filenames from the staged set. It is intentionally a small heuristic and can miss secrets under innocuous names; keep secrets out of the repository and use independent secret scanning. A passing result does not authorize deployment or exposure of production data.

User authorization is defined by the active task. This project request authorizes implementation, a new independent repository, commits, publishing and verification. The development reviewer cannot grant authorization; destructive or production runtime remediation requires human approval.