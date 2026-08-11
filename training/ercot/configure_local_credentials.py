"""Interactively store local ERCOT credentials for offline training only.

Run once from the GERT repository root:

    python -m training.ercot.configure_local_credentials

Values are never printed.  The resulting file is Git-ignored and mode 0600.
"""

from __future__ import annotations

import getpass
import os

from training.ercot.local_credentials import CREDENTIAL_KEYS, CREDENTIAL_PATH


def main() -> None:
    values: dict[str, str] = {}
    for key in CREDENTIAL_KEYS:
        value = getpass.getpass(f"{key}: ").strip()
        if not value or "\n" in value or "\r" in value:
            raise ValueError(f"{key} must be a non-empty single-line value")
        values[key] = value

    CREDENTIAL_PATH.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = CREDENTIAL_PATH.with_suffix(".tmp")
    flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(temporary_path, flags, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
        for key in CREDENTIAL_KEYS:
            handle.write(f"{key}={values[key]}\n")
    os.chmod(temporary_path, 0o600)
    os.replace(temporary_path, CREDENTIAL_PATH)
    print("Stored local ERCOT training credentials securely (not displayed, not tracked by Git).")


if __name__ == "__main__":
    main()
