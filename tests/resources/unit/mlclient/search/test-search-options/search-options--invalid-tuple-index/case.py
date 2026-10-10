"""Independent native JSON/XML representations of Search API options."""

import pytest
from mlclient.search.options import Range, SearchOptions
from mlclient.search.structured import Element

NS = "http://marklogic.com/appservices/search"
PRICE = Range(Element("price"), "xs:decimal")


def run():
    with pytest.raises(TypeError) as error:
        SearchOptions().tuples("price", PRICE, "day")
    assert str(error.value) == "tuples indexes must be Range instances"
