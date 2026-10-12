"""Range options reuse the public structured-query targets."""

from mlclient.search.options import Range
from mlclient.search.structured import PathIndex


def run():
    return Range(
        PathIndex("/p:product/p:price", {"p": "https://example.com/products"}),
        "xs:decimal",
    )
