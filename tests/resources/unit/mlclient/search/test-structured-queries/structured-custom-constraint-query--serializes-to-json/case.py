"""Test custom-constraint-query serialization."""

from tests.utils.resources import read_query_expectation
from mlclient.search.structured import CustomConstraintQuery


def run():
    query = CustomConstraintQuery("custom", ["blue", "green"])
    expected = read_query_expectation(__file__, "expected-1.json")
    assert query.serialize() == expected
    assert query.serialize("json") == expected
