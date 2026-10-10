"""Independent native JSON/XML representations of Search API options."""

import pytest
from mlclient.search.options import Range, SearchOptions
from mlclient.search.structured import Attribute, Element, JsonProperty

NS = "http://marklogic.com/appservices/search"
PRICE = Range(Element("price"), "xs:decimal")


@pytest.mark.parametrize(
    ("target", "attribute"),
    [(JsonProperty("item"), Attribute("code")), (Element("item"), Element("code"))],
)
def run(target, attribute):
    with pytest.raises(TypeError) as error:
        SearchOptions().value_constraint("code", target, attribute=attribute)
    assert (
        str(error.value)
        == "value constraint attribute requires an Element target and an Attribute"
    )
