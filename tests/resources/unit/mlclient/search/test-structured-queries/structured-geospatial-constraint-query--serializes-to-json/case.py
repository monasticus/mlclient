"""Test GeospatialConstraintQuery through its public API."""

from tests.utils.resources import read_query_expectation
from mlclient.search.structured import GeospatialConstraintQuery, Point


def run():
    query = GeospatialConstraintQuery("location", Point(10, 20), text="nearby")
    expected = read_query_expectation(__file__, "expected-1.json")
    assert query.serialize() == expected
    assert query.serialize("json") == expected
