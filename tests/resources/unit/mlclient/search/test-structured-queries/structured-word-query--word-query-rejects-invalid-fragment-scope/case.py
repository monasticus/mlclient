"""Test WordQuery through the public structured-query API."""

import pytest
from mlclient.search.structured import Element, WordQuery


def run():
    with pytest.raises(ValueError, match=r""".+""") as exc:
        WordQuery(Element("title"), "blue", fragment_scope="locks")
    assert str(exc.value) == "Fragment scope must be documents or properties."
