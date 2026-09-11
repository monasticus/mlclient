from dataclasses import FrozenInstanceError

import pytest

from mlclient import MarkLogicVersion


@pytest.mark.parametrize(
    ("raw", "parts"),
    [
        ("12.0.1", (12, 0, 1, None)),
        ("10.0-9.5", (10, 0, 9, 5)),
        ("10.0-11", (10, 0, 11, None)),
        ("12.0", (12, 0, None, None)),
        ("12.0.0.0", (12, 0, 0, 0)),
        ("12.0.1-preview2", (12, 0, 1, None)),
        (" 12.0.1 ", (12, 0, 1, None)),
    ],
)
def test_version_preserves_text_and_unpacks_four_parts(raw, parts):
    version = MarkLogicVersion(raw)

    first, second, third, fourth = version

    assert str(version) == raw.strip()
    assert version.parts == parts
    assert (first, second, third, fourth) == parts


@pytest.mark.parametrize("raw", [None, 12, "", "12", "error 12.0.1", "12.0.1.2.3"])
def test_version_rejects_invalid_input(raw):
    with pytest.raises(ValueError, match="Invalid MarkLogic version"):
        MarkLogicVersion(raw)


def test_version_is_immutable():
    version = MarkLogicVersion("12.0.1")

    with pytest.raises(FrozenInstanceError):
        version.raw = "10.0-9.5"
    with pytest.raises(FrozenInstanceError):
        version.parts = (10, 0, 9, 5)
