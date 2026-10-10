"""Independent native JSON/XML representations of Search API options."""

import pytest
from mlclient.search.options import Range, SearchOptions
from mlclient.search.structured import Element

NS = "http://marklogic.com/appservices/search"
PRICE = Range(Element("price"), "xs:decimal")


def run():
    with pytest.raises(ValueError, match="add requires") as error:
        SearchOptions().add({"return-facets": False})
    assert str(error.value) == (
        "add requires one search-namespace XML element per JSON "
        "definition; return-facets has 1 JSON and 0 XML definiti"
        "ons"
    )
