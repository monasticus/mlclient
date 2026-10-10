"""Test DirectoryQuery through the public structured-query API."""

import pytest
from mlclient.search.structured import DirectoryQuery


def run():
    with pytest.raises(ValueError, match=r""".+""") as exc:
        DirectoryQuery("/reports")
    assert str(exc.value) == "Directory URIs must end with a forward slash."
