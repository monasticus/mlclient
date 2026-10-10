"""Test GeoAttributePairQuery through its public API."""

from mlclient.search.structured import Attribute, Element, GeoAttributePairQuery, Point


def run():
    return GeoAttributePairQuery(
        Element("place"),
        Attribute("lat"),
        Attribute("lon"),
        Point(10, 20),
        options=["units=miles"],
        weight=2,
        fragment_scope="properties",
    )
