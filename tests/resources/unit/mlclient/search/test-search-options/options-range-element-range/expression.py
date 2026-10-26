"""Range options reuse the public structured-query targets."""

from mlclient.search.options import Range, SearchOptions, Values
from mlclient.search.structured import Element


def run():
    return SearchOptions(
        Values(
            "index",
            Range(Element("price", "https://example.com/products"), "xs:decimal"),
        ),
    )
