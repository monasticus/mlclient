"""Independent native JSON/XML representations of Search API options."""

from xml.etree.ElementTree import Element as XmlElement
import pytest
from mlclient.search.options import Range, SearchOptions
from mlclient.search.structured import Element

NS = "http://marklogic.com/appservices/search"
PRICE = Range(Element("price"), "xs:decimal")


def run():
    with pytest.raises(ValueError, match="add requires") as error:
        SearchOptions().add({"page-length": 5}, XmlElement("page-length"))
    assert (
        str(error.value)
        == f"add requires XML elements in the {NS} namespace; got page-length"
    )
