"""Independent native JSON/XML representations of Search API options."""

import pytest
from mlclient.search.options import Range, SearchOptions
from mlclient.search.structured import Element

NS = "http://marklogic.com/appservices/search"
PRICE = Range(Element("price"), "xs:decimal")


def run():
    with pytest.raises(TypeError) as error:
        SearchOptions().range_constraint("price", "price")
    assert str(error.value) == "range constraint index must be a Range"
