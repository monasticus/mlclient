"""Independent native JSON/XML representations of Search API options."""

from mlclient.search.options import Range, SearchOptions
from mlclient.search.structured import Element

NS = "http://marklogic.com/appservices/search"
PRICE = Range(Element("price"), "xs:decimal")


def run():
    assert SearchOptions().values("price", PRICE).control(
        "page-length",
        5,
    ) == SearchOptions().values("price", PRICE).control("page-length", 5)
    assert SearchOptions().values("price", PRICE) != SearchOptions().sort(PRICE)
