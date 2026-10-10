"""Test word-constraint-query serialization."""

from tests.utils.resources import read_query_expectation
from mlclient.search.structured import WordConstraintQuery


def run():
    query = WordConstraintQuery("title", ["blue", "green"], weight=2)
    expected = read_query_expectation(__file__, "expected-1.json")
    assert query.serialize() == expected
    assert query.serialize("json") == expected
