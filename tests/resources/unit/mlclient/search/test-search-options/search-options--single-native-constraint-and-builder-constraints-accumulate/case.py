"""Independent native JSON/XML representations of Search API options."""

from tests.utils.resources import read_query_expectation
from xml.etree.ElementTree import Element as XmlElement
from mlclient.search.options import Range, SearchOptions
from mlclient.search.structured import Element

NS = "http://marklogic.com/appservices/search"
PRICE = Range(Element("price"), "xs:decimal")


def run():
    element = XmlElement(f"{{{NS}}}constraint", {"name": "a"})
    options = (
        SearchOptions()
        .add({"constraint": {"name": "a"}}, element)
        .word_constraint("b", Element("b"))
    )
    assert [
        c["name"] for c in options.to_json()["options"]["constraint"]
    ] == read_query_expectation(__file__, "expected-1.json")
    assert [c.get("name") for c in options.to_xml()] == read_query_expectation(
        __file__,
        "expected-2.json",
    )
