"""Independent native JSON/XML representations of Search API options."""

from xml.etree.ElementTree import Element as XmlElement

from mlclient.search.options import opt

NS = "http://marklogic.com/appservices/search"


def run():
    first = XmlElement(f"{{{NS}}}operator", {"name": "sort"})
    second = XmlElement(f"{{{NS}}}operator", {"name": "page"})
    return opt.options(
        opt.native({"operator": [{"name": "sort"}, {"name": "page"}]}, first, second),
    )
