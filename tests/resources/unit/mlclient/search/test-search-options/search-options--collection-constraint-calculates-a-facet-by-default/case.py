"""Independent native JSON/XML representations of Search API options."""

from tests.utils.resources import read_query_expectation
from mlclient.search.options import Range, SearchOptions
from mlclient.search.structured import Element

NS = "http://marklogic.com/appservices/search"
PRICE = Range(Element("price"), "xs:decimal")


def run():
    options = SearchOptions().collection_constraint("type")
    assert options.to_json()["options"]["constraint"] == read_query_expectation(
        __file__,
        "expected-1.json",
    )
