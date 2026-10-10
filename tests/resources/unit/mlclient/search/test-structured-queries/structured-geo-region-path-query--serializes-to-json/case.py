"""Test GeoRegionPathQuery through its public API."""

from tests.utils.resources import read_query_expectation
from mlclient.search.structured import GeoRegionPathQuery, PathIndex, Point


def run():
    query = GeoRegionPathQuery(
        PathIndex("/place/region"),
        Point(10, 20),
        operator="intersects",
        coord="wgs84",
        options=["units=miles"],
        weight=2,
        fragment_scope="properties",
    )
    expected = read_query_expectation(__file__, "expected-1.json")
    assert query.serialize() == expected
    assert query.serialize("json") == expected
