"""Independent native JSON/XML representations of Search API options."""

from xml.etree.ElementTree import Element as XmlElement
from mlclient.search.options import SearchOptions


def run():
    return SearchOptions().add({"page-length": 5}, XmlElement("page-length"))
