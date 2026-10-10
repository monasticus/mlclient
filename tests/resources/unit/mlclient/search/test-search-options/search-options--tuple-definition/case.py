"""Independent native JSON/XML representations of Search API options."""

from tests.utils.resources import read_query_expectation
from xml.etree.ElementTree import tostring
from mlclient.search.options import Range, SearchOptions
from mlclient.search.structured import Element

NS = "http://marklogic.com/appservices/search"
PRICE = Range(Element("price"), "xs:decimal")


def run():
    options = SearchOptions().tuples("prices", PRICE, Range(Element("day"), "xs:date"))
    assert options.to_json() == read_query_expectation(__file__, "expected-1.json")
    assert tostring(options.to_xml(), encoding="unicode") == read_query_expectation(
        __file__,
        "expected-xml-1.xml",
    )
