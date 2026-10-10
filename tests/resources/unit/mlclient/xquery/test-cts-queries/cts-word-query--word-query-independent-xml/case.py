"""Native word-query serialization through the public CTS builder."""

from tests.utils.resources import read_query_expectation
from xml.etree.ElementTree import tostring
from mlclient.xquery import WordQuery, cts


def run(mocker):
    mocker.patch.object(WordQuery, "to_json", side_effect=AssertionError)
    assert (
        tostring(cts.word_query("blue").to_xml())
        == read_query_expectation(__file__, "expected-1.xml").encode()
    )
