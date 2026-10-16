"""Independent native JSON/XML representations of Search API options."""

from xml.etree.ElementTree import Element as XmlElement

from mlclient.search.options import opt

NS = "http://marklogic.com/appservices/search"


def run():
    element = XmlElement(f"{{{NS}}}return-facets")
    return opt.options(opt.native({}, element))
