"""Local-only credentials for the offline ERCOT training tools.

The credential file is deliberately stored beneath ``training_data/``, which
is ignored by Git.  It is never imported by the production API.
"""

from __future__ import annotations

import os
from pathlib import Path


CREDENTIAL_KEYS = (
    "ERCOT_API_USERNAME",
    "ERCOT_API_PASSWORD",
    "ERCOT_API_SUBSCRIPTION_KEY",
)
CREDENTIAL_PATH = Path("training_data/.ercot_credentials")


def parse_credentials(text: str) -> dict[str, str]:
    """Parse the small local credential file without accepting extra keys."""
    values: dict[str, str] = {}
    for line in text.splitlines():
        if not line.strip():
            continue
        key, separator, value = line.partition("=")
        if not separator or key not in CREDENTIAL_KEYS or not value:
            raise ValueError("Invalid local ERCOT credential file")
        values[key] = value
    if set(values) != set(CREDENTIAL_KEYS):
        raise ValueError("Local ERCOT credential file is incomplete")
    return values


def load_local_credentials(path: Path = CREDENTIAL_PATH) -> None:
    """Populate missing process environment variables from the local file."""
    if all(os.environ.get(key) for key in CREDENTIAL_KEYS):
        return
    if not path.is_file():
        return
    if path.is_symlink():
        raise ValueError("Refusing to load local ERCOT credentials from a symbolic link")
    for key, value in parse_credentials(path.read_text(encoding="utf-8")).items():
        os.environ.setdefault(key, value)
