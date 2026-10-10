"""Range options reuse the public structured-query targets."""

from tests.utils.resources import read_query_expectation
from xml.etree.ElementTree import tostring
from mlclient.search.options import Range
from mlclient.search.structured import PathIndex

NS = "http://marklogic.com/appservices/search"


def run():
    index = Range(PathIndex("/p:product/p:price", {"p": "urn:products"}), "xs:decimal")
    assert index.to_json() == read_query_expectation(__file__, "expected-1.json")
    assert tostring(index.to_xml(), encoding="unicode") == read_query_expectation(
        __file__,
        "expected-xml-1.xml",
    )
