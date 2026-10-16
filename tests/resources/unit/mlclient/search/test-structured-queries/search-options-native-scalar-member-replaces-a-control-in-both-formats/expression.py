"""Independent native JSON/XML representations of Search API options."""

from xml.etree.ElementTree import Element as XmlElement

from mlclient.search.options import opt

NS = "http://marklogic.com/appservices/search"


def run():
    replacement = XmlElement(f"{{{NS}}}page-length")
    replacement.text = "50"
    return opt.options(
        opt.control("page-length", 10),
        opt.control("return-facets", False),
        opt.native({"page-length": 50}, replacement),
    )
