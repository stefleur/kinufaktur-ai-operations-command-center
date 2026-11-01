from pathlib import Path
from typing import Literal

from mcp.server.fastmcp import FastMCP


PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONTEXT_FILES = {
    "spec": "docs/product-spec.md",
    "api_contract": "openapi.json",
    "instructions": "AGENTS.md",
}

mcp = FastMCP("kinufaktur-operations-project-context")


def _read_context_file(section: Literal["spec", "api_contract", "instructions"]) -> str:
    project_root = PROJECT_ROOT.resolve(strict=True)
    context_path = project_root / CONTEXT_FILES[section]
    if context_path.is_symlink():
        raise ValueError("Project context files cannot be symlinks.")

    resolved_path = context_path.resolve(strict=True)
    try:
        resolved_path.relative_to(project_root)
    except ValueError as error:
        raise ValueError("Project context resolved outside the project root.") from error
    if not resolved_path.is_file():
        raise ValueError("Project context must resolve to a regular file.")

    return resolved_path.read_text(encoding="utf-8")


@mcp.tool()
def get_project_context(
    section: Literal["spec", "api_contract", "instructions"],
) -> str:
    """Read one fixed Kinufaktur AI Operations Command Center project context file by its allowed section."""
    return _read_context_file(section)


if __name__ == "__main__":
    mcp.run(transport="stdio")