"""Independent native JSON/XML representations of Search API options."""

from tests.utils.resources import read_query_expectation
from xml.etree.ElementTree import tostring
from mlclient.search.options import Range, SearchOptions
from mlclient.search.structured import Attribute, Element

NS = "http://marklogic.com/appservices/search"
PRICE = Range(Element("price"), "xs:decimal")


def run():
    options = SearchOptions().word_constraint(
        "code",
        Element("item"),
        attribute=Attribute("code"),
    )
    assert options.to_json()["options"]["constraint"] == read_query_expectation(
        __file__,
        "expected-1.json",
    )
    assert tostring(options.to_xml(), encoding="unicode") == read_query_expectation(
        __file__,
        "expected-xml-1.xml",
    )
