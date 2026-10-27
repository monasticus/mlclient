"""Independent native JSON/XML representations of Search API options."""

from mlclient.search.options import Range, SearchOptions, Values
from mlclient.search.structured import Element

PRICE = Range(Element("price"), "xs:decimal")


def run():
    return SearchOptions(Values("price", PRICE, options=["frequency-order"]))
