from pathlib import Path

import pytest

from training.ercot.local_credentials import load_local_credentials, parse_credentials


def test_parse_credentials_requires_exact_complete_key_set() -> None:
    text = "\n".join(
        (
            "ERCOT_API_USERNAME=user@example.test",
            "ERCOT_API_PASSWORD=password",
            "ERCOT_API_SUBSCRIPTION_KEY=subscription",
        )
    )

    assert parse_credentials(text)["ERCOT_API_USERNAME"] == "user@example.test"


@pytest.mark.parametrize("text", ("", "OTHER=value", "ERCOT_API_USERNAME=user"))
def test_parse_credentials_rejects_incomplete_or_unknown_values(text: str) -> None:
    with pytest.raises(ValueError):
        parse_credentials(text)


def test_load_local_credentials_rejects_symbolic_link(tmp_path: Path) -> None:
    target = tmp_path / "target"
    target.write_text(
        "ERCOT_API_USERNAME=u\nERCOT_API_PASSWORD=p\nERCOT_API_SUBSCRIPTION_KEY=k\n"
    )
    link = tmp_path / "link"
    link.symlink_to(target)

    with pytest.raises(ValueError, match="symbolic link"):
        load_local_credentials(link)
