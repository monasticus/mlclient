"""Independent native JSON/XML representations of Search API options."""

from mlclient.search.options import Range, RangeConstraint, SearchOptions
from mlclient.search.structured import Element

PRICE = Range(Element("price"), "xs:decimal")


def run():
    return SearchOptions(RangeConstraint("price", PRICE, facet=False))
