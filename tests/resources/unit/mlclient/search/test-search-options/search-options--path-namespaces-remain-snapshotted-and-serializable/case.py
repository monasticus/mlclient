"""Independent native JSON/XML representations of Search API options."""

from xml.etree.ElementTree import tostring
import pytest
from mlclient.search.options import Range, SearchOptions
from mlclient.search.structured import Element, PathIndex

NS = "http://marklogic.com/appservices/search"
PRICE = Range(Element("price"), "xs:decimal")


@pytest.mark.parametrize(
    "build",
    [
        lambda index: SearchOptions().values("price", index),
        lambda index: SearchOptions().tuples("pair", index, index),
        lambda index: SearchOptions().range_constraint("price", index),
        lambda index: SearchOptions().sort(index),
    ],
)
def run(build):
    namespaces = {"p": "urn:prices"}
    index = Range(PathIndex("/p:price", namespaces), "xs:decimal")
    options = build(index)
    namespaces["p"] = "urn:changed"
    assert "urn:prices" in str(options.to_json())
    assert "urn:changed" not in str(options.to_json())
    xml = tostring(options.to_xml(), encoding="unicode")
    assert "urn:prices" in xml
    assert "urn:changed" not in xml
