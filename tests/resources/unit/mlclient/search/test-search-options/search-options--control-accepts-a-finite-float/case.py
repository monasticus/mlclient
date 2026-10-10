"""Independent native JSON/XML representations of Search API options."""

from tests.utils.resources import read_query_expectation
from mlclient.search.options import Range, SearchOptions
from mlclient.search.structured import Element

NS = "http://marklogic.com/appservices/search"
PRICE = Range(Element("price"), "xs:decimal")


def run():
    options = SearchOptions().control("quality-weight", 0.5)
    assert options.to_json() == read_query_expectation(__file__, "expected-1.json")
