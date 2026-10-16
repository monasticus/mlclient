"""Independent native JSON/XML representations of Search API options."""

from xml.etree.ElementTree import Element as XmlElement

from mlclient.search.options import Control, NativeOptions, SearchOptions

NS = "http://marklogic.com/appservices/search"


def run():
    replacement = XmlElement(f"{{{NS}}}page-length")
    replacement.text = "50"
    return SearchOptions(
        Control("page-length", 10),
        Control("return-facets", False),
        NativeOptions({"page-length": 50}, replacement),
    )
