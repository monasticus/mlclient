"""Test GeoElementPairQuery through its public API."""

from mlclient.search.structured import Element, GeoElementPairQuery, Point


def run():
    return GeoElementPairQuery(
        Element("place"),
        Element("lat"),
        Element("lon"),
        Point(10, 20),
        options=["units=miles"],
        weight=2,
        fragment_scope="properties",
    )
