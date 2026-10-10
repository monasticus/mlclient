"""Native word-query serialization through the public CTS builder."""

from tests.utils.resources import read_query_expectation
from xml.etree.ElementTree import tostring
from mlclient.xquery import cts


def run():
    assert (
        tostring(cts.word_query("blue", weight=1e-05).to_xml())
        == read_query_expectation(__file__, "expected-1.xml").encode()
    )
