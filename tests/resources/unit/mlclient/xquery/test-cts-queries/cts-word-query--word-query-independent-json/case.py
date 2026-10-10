"""Native word-query serialization through the public CTS builder."""

from tests.utils.resources import read_query_expectation
from mlclient.xquery import WordQuery, cts


def run(mocker):
    mocker.patch.object(WordQuery, "to_xml", side_effect=AssertionError)
    assert cts.word_query("blue").to_json() == read_query_expectation(
        __file__,
        "expected-1.json",
    )
