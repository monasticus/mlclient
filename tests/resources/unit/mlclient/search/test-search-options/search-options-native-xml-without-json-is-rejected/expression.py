"""Independent native JSON/XML representations of Search API options."""

from xml.etree.ElementTree import Element as XmlElement
from mlclient.search.options import SearchOptions

NS = "http://marklogic.com/appservices/search"


def run():
    element = XmlElement(f"{{{NS}}}return-facets")
    return SearchOptions().add({}, element)
