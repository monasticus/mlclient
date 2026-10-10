"""Test ContainerQuery through the public structured-query API."""

import pytest
from mlclient.search.structured import ContainerQuery, Field, TermQuery


def run():
    with pytest.raises(TypeError, match=r""".+""") as exc:
        ContainerQuery(Field("body"), TermQuery("blue"))
    assert (
        str(exc.value) == "Container queries require element or JSON property targets."
    )
