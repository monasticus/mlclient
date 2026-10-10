"""Range options reuse the public structured-query targets."""

import pytest
from mlclient.search.options import Range
from mlclient.search.structured import Element

NS = "http://marklogic.com/appservices/search"


def run():
    with pytest.raises(TypeError) as error:
        Range(Element("product"), attribute="category").to_json()
    assert (
        str(error.value)
        == "range attribute requires an Element target and an Attribute"
    )
