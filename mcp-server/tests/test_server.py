import asyncio
import importlib.util
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SERVER_PATH = PROJECT_ROOT / "mcp-server" / "server.py"
SERVER_SPEC = importlib.util.spec_from_file_location("kinufaktur_operations_context_server_test", SERVER_PATH)
if SERVER_SPEC is None or SERVER_SPEC.loader is None:
    raise RuntimeError("Could not load the MCP server module for focused tests.")
server_module = importlib.util.module_from_spec(SERVER_SPEC)
SERVER_SPEC.loader.exec_module(server_module)


async def verify_server_protocol() -> None:
    parameters = StdioServerParameters(
        command=sys.executable,
        args=[str(SERVER_PATH)],
        cwd=str(PROJECT_ROOT),
    )
    async with stdio_client(parameters) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            initialized = await session.initialize()
            assert initialized.serverInfo.name == "kinufaktur-operations-project-context"

            tools = await session.list_tools()
            assert [tool.name for tool in tools.tools] == ["get_project_context"]

            expected_text = {
                "spec": "# Product specification",
                "api_contract": '"openapi": "3.1.0"',
                "instructions": "# Kinufaktur AI Operations Command Center",
            }
            for section, expected in expected_text.items():
                result = await session.call_tool(
                    "get_project_context", {"section": section}
                )
                assert not result.isError
                assert expected in result.content[0].text

            invalid = await session.call_tool(
                "get_project_context", {"section": "arbitrary/path"}
            )
            assert invalid.isError


def test_server_initializes_and_exposes_only_fixed_read_tool() -> None:
    asyncio.run(verify_server_protocol())


def test_symlinked_allowlisted_file_outside_project_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project_root = tmp_path / "operations-project"
    project_root.mkdir()
    outside_file = tmp_path / "outside-spec.md"
    outside_file.write_text("outside content", encoding="utf-8")
    (project_root / "docs").mkdir()
    (project_root / "docs" / "product-spec.md").symlink_to(outside_file)
    monkeypatch.setattr(server_module, "PROJECT_ROOT", project_root)

    with pytest.raises(ValueError, match="cannot be symlinks"):
        server_module.get_project_context("spec")