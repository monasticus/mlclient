"""Test NearQuery through the public structured-query API."""

from tests.utils.resources import read_query_expectation
from mlclient.search.structured import NearQuery, TermQuery


def run():
    query = NearQuery(
        [TermQuery("blue"), TermQuery("green")],
        distance=3,
        minimum_distance=1,
        distance_weight=2,
        ordered=False,
    )
    expected = read_query_expectation(__file__, "expected-1.json")
    assert query.serialize() == expected
    assert query.serialize("json") == expected
