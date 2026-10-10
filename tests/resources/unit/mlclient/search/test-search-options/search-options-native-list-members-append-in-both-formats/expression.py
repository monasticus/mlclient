"""Independent native JSON/XML representations of Search API options."""

from xml.etree.ElementTree import Element as XmlElement
from mlclient.search.options import SearchOptions

NS = "http://marklogic.com/appservices/search"


def run():
    first = XmlElement(f"{{{NS}}}operator", {"name": "sort"})
    second = XmlElement(f"{{{NS}}}operator", {"name": "page"})
    return SearchOptions().add(
        {"operator": [{"name": "sort"}, {"name": "page"}]},
        first,
        second,
    )
