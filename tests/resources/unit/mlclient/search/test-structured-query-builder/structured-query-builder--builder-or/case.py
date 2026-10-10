"""Test structured-query composition through the public builder."""

from tests.utils.resources import read_query_expectation
from mlclient.search.structured import sq


def run():
    query = sq.or_(sq.collection("reports"), sq.not_(sq.term("blue")))
    assert query.serialize() == read_query_expectation(__file__, "expected-1.json")
