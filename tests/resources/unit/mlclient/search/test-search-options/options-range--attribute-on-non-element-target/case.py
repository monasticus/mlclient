"""Range options reuse the public structured-query targets."""

import pytest
from mlclient.search.options import Range
from mlclient.search.structured import Attribute, JsonProperty

NS = "http://marklogic.com/appservices/search"


def run():
    with pytest.raises(TypeError) as error:
        Range(JsonProperty("product"), attribute=Attribute("category")).to_xml()
    assert (
        str(error.value)
        == "range attribute requires an Element target and an Attribute"
    )
