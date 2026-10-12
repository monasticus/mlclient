"""Range options reuse the public structured-query targets."""

from mlclient.search.options import Range
from mlclient.search.structured import Attribute, Element


def run():
    return Range(
        Element("product"),
        attribute=Attribute("category"),
        collation="https://example.com/collation",
    )
