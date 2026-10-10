"""Test DocumentQuery through the public structured-query API."""

from tests.utils.resources import read_query_expectation
from mlclient.search.structured import DocumentQuery


def run():
    query = DocumentQuery(["/reports/first.xml", "/reports/second.json"])
    expected = read_query_expectation(__file__, "expected-1.json")
    assert query.serialize() == expected
    assert query.serialize("json") == expected
