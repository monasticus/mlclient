"""Test GeoPathQuery through its public API."""

from tests.utils.resources import read_query_expectation
from mlclient.search.structured import GeoPathQuery, PathIndex, Point


def run():
    query = GeoPathQuery(
        PathIndex("/place/location"),
        Point(10, 20),
        options=["units=miles"],
        weight=2,
        fragment_scope="properties",
    )
    expected = read_query_expectation(__file__, "expected-1.json")
    assert query.serialize() == expected
    assert query.serialize("json") == expected
