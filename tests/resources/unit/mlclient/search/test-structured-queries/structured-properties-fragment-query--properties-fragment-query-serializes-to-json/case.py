"""Test PropertiesFragmentQuery through the public structured-query API."""

from tests.utils.resources import read_query_expectation
from mlclient.search.structured import PropertiesFragmentQuery, TermQuery


def run():
    query = PropertiesFragmentQuery(TermQuery("blue"))
    expected = read_query_expectation(__file__, "expected-1.json")
    assert query.serialize() == expected
    assert query.serialize("json") == expected
