"""Test collection-constraint-query serialization."""

from tests.utils.resources import read_query_expectation
from mlclient.search.structured import CollectionConstraintQuery


def run():
    query = CollectionConstraintQuery("category", ["blue", "green"])
    expected = read_query_expectation(__file__, "expected-1.json")
    assert query.serialize() == expected
    assert query.serialize("json") == expected
