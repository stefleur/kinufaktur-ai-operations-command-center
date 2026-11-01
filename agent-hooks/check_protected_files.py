import subprocess
import sys
from pathlib import Path, PurePosixPath


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
PRIVATE_KEY_SUFFIXES = {".key", ".pem", ".p12", ".pfx"}
PRIVATE_KEY_NAMES = {"id_rsa", "id_ed25519", "id_ecdsa"}


def find_protected_paths(paths: list[str]) -> list[str]:
    protected = []
    for path in paths:
        parts = PurePosixPath(path.replace("\\", "/")).parts
        name = parts[-1].lower() if parts else ""

        is_env_file = name == ".env" or (
            name.startswith(".env.")
            and not name.endswith((".example", ".sample"))
        )
        is_credential_file = name in {"credentials", "credentials.json"}
        is_secret_file = name.startswith(("secret.", "secrets."))
        is_service_account = name.startswith("service-account") and name.endswith(
            ".json"
        )
        has_private_key_name = name in PRIVATE_KEY_NAMES
        has_private_key_suffix = PurePosixPath(name).suffix in PRIVATE_KEY_SUFFIXES
        has_protected_directory = any(
            part.lower() in {".ssh", "secrets"} for part in parts[:-1]
        )

        if (
            is_env_file
            or is_credential_file
            or is_secret_file
            or is_service_account
            or has_private_key_name
            or has_private_key_suffix
            or has_protected_directory
        ):
            protected.append(path)
    return protected


def main() -> int:
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "-z"],
        cwd=REPOSITORY_ROOT,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="surrogateescape",
    )
    staged_paths = result.stdout.split("\0")
    staged_paths = [path for path in staged_paths if path]
    protected = find_protected_paths(staged_paths)
    if protected:
        print("Rejected protected paths:", file=sys.stderr)
        for path in protected:
            print(f"  {path}", file=sys.stderr)
        return 1

    print("No obvious protected secret or credential paths are staged.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())