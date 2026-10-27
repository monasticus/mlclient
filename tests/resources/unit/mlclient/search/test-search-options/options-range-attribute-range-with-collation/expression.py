"""Range options reuse the public structured-query targets."""

from mlclient.search.options import Range, SearchOptions, Values
from mlclient.search.structured import Attribute, Element


def run():
    return SearchOptions(
        Values(
            "index",
            Range(
                Element("product"),
                attribute=Attribute("category"),
                collation="https://example.com/collation",
            ),
        ),
    )
