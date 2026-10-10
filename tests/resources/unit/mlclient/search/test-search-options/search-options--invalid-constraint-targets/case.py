"""Independent native JSON/XML representations of Search API options."""

import pytest
from mlclient.search.options import Range, SearchOptions
from mlclient.search.structured import Element, Field

NS = "http://marklogic.com/appservices/search"
PRICE = Range(Element("price"), "xs:decimal")


@pytest.mark.parametrize(
    ("build", "message"),
    [
        (
            lambda: SearchOptions().word_constraint("label", "label"),
            "word constraint target must be an Element, JsonProperty or Field",
        ),
        (
            lambda: SearchOptions().value_constraint("label", None),
            "value constraint target must be an Element, JsonProperty or Field",
        ),
        (
            lambda: SearchOptions().container_constraint("place", Field("place")),
            "container constraint target must be an Element or JsonProperty",
        ),
    ],
)
def run(build, message):
    with pytest.raises(TypeError) as error:
        build()
    assert str(error.value) == message
