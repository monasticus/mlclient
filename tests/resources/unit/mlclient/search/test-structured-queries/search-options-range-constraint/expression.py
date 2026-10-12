"""Independent native JSON/XML representations of Search API options."""

from mlclient.search.options import Range, SearchOptions
from mlclient.search.structured import Element

PRICE = Range(Element("price"), "xs:decimal")


def run():
    return SearchOptions().range_constraint("price", PRICE, options=["limit=10"])
