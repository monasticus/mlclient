"""Independent native JSON/XML representations of Search API options."""

import pytest
from mlclient.search.options import Range, SearchOptions
from mlclient.search.structured import Element, JsonProperty

NS = "http://marklogic.com/appservices/search"
PRICE = Range(Element("price"), "xs:decimal")


def run():
    with pytest.raises(ValueError, match="node_type must be one of") as error:
        SearchOptions().value_constraint(
            "price",
            JsonProperty("price"),
            node_type="int",
        )
    assert str(error.value) == (
        "value constraint node_type must be one of boolean, null"
        ", number, string, got 'int'"
    )
