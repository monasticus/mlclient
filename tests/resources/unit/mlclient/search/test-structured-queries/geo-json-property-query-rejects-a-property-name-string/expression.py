"""Test GeoJsonPropertyQuery through its public API."""

from mlclient.search.structured import GeoJsonPropertyQuery, Point


def run():
    return GeoJsonPropertyQuery("location", Point(10, 20))
