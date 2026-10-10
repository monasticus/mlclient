"""Test GeoRegionConstraintQuery through its public API."""

from tests.utils.resources import read_query_expectation
from mlclient.search.structured import GeoRegionConstraintQuery, Point


def run():
    query = GeoRegionConstraintQuery(
        "location",
        Point(10, 20),
        operator="intersects",
        weight=2,
    )
    expected = read_query_expectation(__file__, "expected-1.json")
    assert query.serialize() == expected
    assert query.serialize("json") == expected
