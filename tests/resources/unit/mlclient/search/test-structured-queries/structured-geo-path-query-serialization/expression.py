"""Test GeoPathQuery through its public API."""

from mlclient.search.structured import GeoPathQuery, PathIndex, Point


def run():
    return GeoPathQuery(
        PathIndex("/place/location"),
        Point(10, 20),
        options=["units=miles"],
        weight=2,
        fragment_scope="properties",
    )
