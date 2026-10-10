"""Test TermQuery through the public structured-query API."""

from decimal import Decimal
from mlclient.search.structured import Element, RangeQuery


def run():
    query = RangeQuery(Element("price"), Decimal("NaN"), operator="LT")
    assert query.to_json()["range-query"]["value"] == "NaN"
