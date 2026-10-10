"""Native word-query serialization through the public CTS builder."""

from tests.utils.resources import read_query_expectation
from mlclient.xquery import cts


def run():
    query = cts.word_query("blue", options=["unstemmed", "case-insensitive", "lang=en"])
    assert query.serialize() == read_query_expectation(__file__, "expected-1.json")
