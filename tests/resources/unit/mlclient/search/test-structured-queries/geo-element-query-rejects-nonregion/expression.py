"""Test GeoElementQuery through its public API."""

from mlclient.search.structured import Element, GeoElementQuery


def run():
    return GeoElementQuery(Element("location"), "10,20")
