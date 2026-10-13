from mlclient.search.options import Range, SearchOptions
from mlclient.search.structured import Element


def run():
    return SearchOptions().values(
        "price",
        Range(Element("price"), "xs:decimal"),
        options="frequency-order",
    )
