"""Test properties-constraint-query serialization."""

from tests.utils.resources import read_query_expectation
from mlclient.search.structured import PropertiesConstraintQuery, TrueQuery


def run():
    query = PropertiesConstraintQuery("metadata", TrueQuery())
    expected = read_query_expectation(__file__, "expected-1.json")
    assert query.serialize() == expected
    assert query.serialize("json") == expected
