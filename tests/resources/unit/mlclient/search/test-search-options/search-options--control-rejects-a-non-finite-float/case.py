"""Independent native JSON/XML representations of Search API options."""

import pytest
from mlclient.search.options import Range, SearchOptions
from mlclient.search.structured import Element

NS = "http://marklogic.com/appservices/search"
PRICE = Range(Element("price"), "xs:decimal")


@pytest.mark.parametrize("value", [float("nan"), float("inf")])
def run(value):
    with pytest.raises(ValueError, match="must be finite"):
        SearchOptions().control("quality-weight", value)
