"""Test WordQuery through the public structured-query API."""

from tests.utils.resources import read_query_expectation
from mlclient.search.structured import Element, WordQuery


def run():
    query = WordQuery([Element("title"), Element("label"), Element("body")], "blue")
    assert query.serialize() == read_query_expectation(__file__, "expected-1.json")
