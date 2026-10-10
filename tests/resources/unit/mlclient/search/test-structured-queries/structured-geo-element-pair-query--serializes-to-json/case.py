"""Test GeoElementPairQuery through its public API."""

from tests.utils.resources import read_query_expectation
from mlclient.search.structured import Element, GeoElementPairQuery, Point


def run():
    query = GeoElementPairQuery(
        Element("place"),
        Element("lat"),
        Element("lon"),
        Point(10, 20),
        options=["units=miles"],
        weight=2,
        fragment_scope="properties",
    )
    expected = read_query_expectation(__file__, "expected-1.json")
    assert query.serialize() == expected
    assert query.serialize("json") == expected
