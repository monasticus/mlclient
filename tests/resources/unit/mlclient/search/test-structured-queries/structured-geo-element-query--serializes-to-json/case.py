"""Test GeoElementQuery through its public API."""

from tests.utils.resources import read_query_expectation
from mlclient.search.structured import Element, GeoElementQuery, Point


def run():
    query = GeoElementQuery(
        Element("location"),
        Point(10, 20),
        parent=Element("place"),
        options=["units=miles"],
        weight=2,
        fragment_scope="properties",
    )
    expected = read_query_expectation(__file__, "expected-1.json")
    assert query.serialize() == expected
    assert query.serialize("json") == expected
