"""Test structured-query composition through the public builder."""

from tests.utils.resources import read_query_expectation
from mlclient.search.structured import StructuredQueryBuilder


def run():
    builder = StructuredQueryBuilder()
    query = builder.and_(builder.term("blue"), builder.term("green"), ordered=True)
    assert query.serialize() == read_query_expectation(__file__, "expected-1.json")
