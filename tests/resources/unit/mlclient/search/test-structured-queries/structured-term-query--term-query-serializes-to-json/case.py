"""Test TermQuery through the public structured-query API."""

from tests.utils.resources import read_query_expectation
from mlclient.search.structured import TermQuery


def run():
    query = TermQuery(
        ["blue", "green"],
        weight=2,
        options=["case-sensitive", "unstemmed"],
    )
    expected = read_query_expectation(__file__, "expected-1.json")
    assert query.serialize() == expected
    assert query.serialize("json") == expected
