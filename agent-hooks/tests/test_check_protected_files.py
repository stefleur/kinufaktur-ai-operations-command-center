import subprocess
import sys
from pathlib import Path

import pytest


HOOK_DIRECTORY = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOOK_DIRECTORY))

from check_protected_files import find_protected_paths, main


def test_guardrail_accepts_safe_paths() -> None:
    assert find_protected_paths(
        ["docs/permissions.md", "backend/app/main.py", ".env.example"]
    ) == []


@pytest.mark.parametrize(
    "path",
    [
        ".env",
        ".env.production",
        "secrets/token.txt",
        "config/credentials.json",
        "keys/service-account-prod.json",
        "keys/deploy.pem",
        ".ssh/id_ed25519",
    ],
)
def test_guardrail_rejects_protected_paths(path: str) -> None:
    assert find_protected_paths([path]) == [path]


def test_cli_checks_staged_paths(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        "check_protected_files.subprocess.run",
        lambda *args, **kwargs: subprocess.CompletedProcess(
            args[0], 0, stdout=".env\0docs/permissions.md\0", stderr=""
        ),
    )

    assert main() == 1
    assert ".env" in capsys.readouterr().err

def test_guardrail_uses_independent_repository_root():
    import check_protected_files
    assert check_protected_files.REPOSITORY_ROOT == HOOK_DIRECTORY.parent
