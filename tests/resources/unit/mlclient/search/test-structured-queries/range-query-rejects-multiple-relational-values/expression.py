"""Test RangeQuery through the public structured-query API."""

from mlclient.search.structured import Element, RangeQuery


def run():
    return RangeQuery(Element("price"), [1, 2], operator="GT")
