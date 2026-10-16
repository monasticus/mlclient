from mlclient.search.options import Range, SearchOptions, Values
from mlclient.search.structured import Element


def run():
    return SearchOptions(
        Values(
            "price",
            Range(Element("price"), "xs:decimal"),
            options="frequency-order",
        ),
    )
