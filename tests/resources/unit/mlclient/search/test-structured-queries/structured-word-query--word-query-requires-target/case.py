"""Test WordQuery through the public structured-query API."""

import pytest
from mlclient.search.structured import WordQuery


def run():
    with pytest.raises(ValueError, match=r""".+""") as exc:
        WordQuery([], "blue")
    assert str(exc.value) == "Use one non-empty target kind."
