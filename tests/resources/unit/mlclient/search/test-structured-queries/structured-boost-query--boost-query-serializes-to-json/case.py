"""Test BoostQuery through the public structured-query API."""

from tests.utils.resources import read_query_expectation
from mlclient.search.structured import BoostQuery, TermQuery


def run():
    query = BoostQuery(TermQuery("blue"), TermQuery("green", weight=2))
    expected = read_query_expectation(__file__, "expected-1.json")
    assert query.serialize() == expected
    assert query.serialize("json") == expected
