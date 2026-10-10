"""Test GeospatialConstraintQuery through its public API."""

from mlclient.search.structured import GeospatialConstraintQuery, Point


def run():
    return GeospatialConstraintQuery("location", Point(10, 20), text="nearby")
