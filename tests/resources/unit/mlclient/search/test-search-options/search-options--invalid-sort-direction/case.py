"""Independent native JSON/XML representations of Search API options."""

import pytest
from mlclient.search.options import Range, SearchOptions
from mlclient.search.structured import Element

NS = "http://marklogic.com/appservices/search"
PRICE = Range(Element("price"), "xs:decimal")


def run():
    with pytest.raises(ValueError, match="sort direction") as error:
        SearchOptions().sort(PRICE, direction="up")
    assert str(error.value) == "sort direction must be ascending or descending"
