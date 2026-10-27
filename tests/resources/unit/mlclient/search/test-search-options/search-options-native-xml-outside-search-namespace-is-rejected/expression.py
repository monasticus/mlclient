"""Independent native JSON/XML representations of Search API options."""

from xml.etree.ElementTree import Element as XmlElement

from mlclient.search.options import NativeOptions, SearchOptions


def run():
    return SearchOptions(NativeOptions({"page-length": 5}, XmlElement("page-length")))
