"""Test RangeQuery through the public structured-query API."""

from mlclient.search.structured import Attribute, Element, RangeQuery


def run():
    return RangeQuery(
        Element("price"),
        [3, 4],
        operator="EQ",
        index_type="xs:int",
        collation="https://example.com/example",
        options=["cached"],
        weight=2,
        fragment_scope="documents",
        attribute=Attribute("amount"),
    )
