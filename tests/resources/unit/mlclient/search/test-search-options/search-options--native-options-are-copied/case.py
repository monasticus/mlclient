"""Independent native JSON/XML representations of Search API options."""

from tests.utils.resources import read_query_expectation
from xml.etree.ElementTree import Element as XmlElement, tostring
from mlclient.search.options import Range, SearchOptions
from mlclient.search.structured import Element

NS = "http://marklogic.com/appservices/search"
PRICE = Range(Element("price"), "xs:decimal")


def run():
    definition = {"transform-results": {"apply": "empty-snippet"}}
    element = XmlElement(f"{{{NS}}}transform-results", {"apply": "empty-snippet"})
    options = SearchOptions().add(definition, element)
    definition["transform-results"]["apply"] = "raw"
    element.set("apply", "raw")
    assert options.to_json() == read_query_expectation(__file__, "expected-1.json")
    assert tostring(options.to_xml(), encoding="unicode") == read_query_expectation(
        __file__,
        "expected-xml-1.xml",
    )
