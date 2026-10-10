"""Test QtextQuery through its public API."""

from tests.utils.resources import read_query_expectation
from mlclient.search.structured import QtextQuery


def run():
    query = QtextQuery("blue AND green")
    expected = read_query_expectation(__file__, "expected-1.json")
    assert query.serialize() == expected
    assert query.serialize("json") == expected
