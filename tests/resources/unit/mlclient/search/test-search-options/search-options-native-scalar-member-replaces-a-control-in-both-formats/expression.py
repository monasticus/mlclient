"""Independent native JSON/XML representations of Search API options."""

from xml.etree.ElementTree import Element as XmlElement
from mlclient.search.options import SearchOptions

NS = "http://marklogic.com/appservices/search"


def run():
    replacement = XmlElement(f"{{{NS}}}page-length")
    replacement.text = "50"
    return (
        SearchOptions()
        .control("page-length", 10)
        .control("return-facets", False)
        .add({"page-length": 50}, replacement)
    )
