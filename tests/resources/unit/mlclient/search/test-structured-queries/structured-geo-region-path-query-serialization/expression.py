"""Test GeoRegionPathQuery through its public API."""

from mlclient.search.structured import GeoRegionPathQuery, PathIndex, Point


def run():
    return GeoRegionPathQuery(
        PathIndex("/place/region"),
        Point(10, 20),
        operator="intersects",
        coord="wgs84",
        options=["units=miles"],
        weight=2,
        fragment_scope="properties",
    )
