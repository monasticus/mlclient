"""Test GeoElementQuery through its public API."""

from tests.utils.resources import read_query_expectation
from mlclient.search.structured import Element, GeoElementQuery, Point


def run():
    query = GeoElementQuery(Element("location"), Point(10, 20))
    assert query.serialize() == read_query_expectation(__file__, "expected-1.json")
