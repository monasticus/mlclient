"""Independent native JSON/XML representations of Search API options."""

from xml.etree.ElementTree import Element as XmlElement

from mlclient.search.options import opt


def run():
    return opt.options(opt.native({"page-length": 5}, XmlElement("page-length")))
