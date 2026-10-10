"""Range options reuse the public structured-query targets."""

import pytest
from mlclient.search.options import Range

NS = "http://marklogic.com/appservices/search"


def run():
    with pytest.raises(TypeError) as error:
        Range("price").to_json()
    assert (
        str(error.value)
        == "range target must be an Element, Field, JsonProperty or PathIndex"
    )
