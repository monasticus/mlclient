"""Independent native JSON/XML representations of Search API options."""

from xml.etree.ElementTree import Element as XmlElement
import pytest
from mlclient.search.options import Range, SearchOptions
from mlclient.search.structured import Element

NS = "http://marklogic.com/appservices/search"
PRICE = Range(Element("price"), "xs:decimal")


def run():
    element = XmlElement(f"{{{NS}}}return-facets")
    with pytest.raises(ValueError, match="add requires") as error:
        SearchOptions().add({}, element)
    assert str(error.value) == (
        "add requires one search-namespace XML element per JSON "
        "definition; return-facets has 0 JSON and 1 XML definiti"
        "ons"
    )
