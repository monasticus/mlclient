"""Independent native JSON/XML representations of Search API options."""

from mlclient.search.options import Range, opt
from mlclient.search.structured import Element

PRICE = Range(Element("price"), "xs:decimal")


def run():
    return opt.options(opt.range_constraint("price", PRICE, facet=False))
