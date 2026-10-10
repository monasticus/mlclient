"""Independent native JSON/XML representations of Search API options."""

from tests.utils.resources import read_query_expectation
from mlclient.search.options import Range, SearchOptions
from mlclient.search.structured import Element, Field

NS = "http://marklogic.com/appservices/search"
PRICE = Range(Element("price"), "xs:decimal")


def run():
    options = SearchOptions().word_constraint("summary", Field("summary"))
    assert options.to_json() == read_query_expectation(__file__, "expected-1.json")
