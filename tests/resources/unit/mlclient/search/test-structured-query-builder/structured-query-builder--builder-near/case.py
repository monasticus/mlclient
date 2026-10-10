"""Test structured-query composition through the public builder."""

from tests.utils.resources import read_query_expectation
from mlclient.search.structured import sq


def run():
    query = sq.near(
        sq.term("blue"),
        sq.term("green"),
        distance=3,
        minimum_distance=1,
        distance_weight=2,
        ordered=False,
    )
    assert query.serialize() == read_query_expectation(__file__, "expected-1.json")
