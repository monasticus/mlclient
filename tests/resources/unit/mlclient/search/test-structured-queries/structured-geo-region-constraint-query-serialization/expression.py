"""Test GeoRegionConstraintQuery through its public API."""

from mlclient.search.structured import GeoRegionConstraintQuery, Point


def run():
    return GeoRegionConstraintQuery(
        "location",
        Point(10, 20),
        operator="intersects",
        weight=2,
    )
