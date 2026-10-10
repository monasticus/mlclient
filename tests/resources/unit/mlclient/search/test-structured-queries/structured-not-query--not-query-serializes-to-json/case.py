"""Test NotQuery through the public structured-query API."""

from tests.utils.resources import read_query_expectation
from mlclient.search.structured import NotQuery, TermQuery


def run():
    query = NotQuery(TermQuery("blue"))
    expected = read_query_expectation(__file__, "expected-1.json")
    assert query.serialize() == expected
    assert query.serialize("json") == expected
