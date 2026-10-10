"""Test word-constraint-query serialization."""

import pytest
from mlclient.search.structured import WordConstraintQuery


def run():
    with pytest.raises(ValueError, match=r""".+""") as exc:
        WordConstraintQuery(["title", "label"], "blue").serialize("xml")
    assert (
        str(exc.value)
        == "Use one non-empty constraint name; combine queries with OrQuery."
    )
