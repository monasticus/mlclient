"""Test GeoElementQuery through its public API."""

from mlclient.search.structured import Element, GeoElementQuery, Point


def run():
    return GeoElementQuery(
        Element("location"),
        Point(10, 20),
        parent=Element("place"),
        options=["units=miles"],
        weight=2,
        fragment_scope="properties",
    )
