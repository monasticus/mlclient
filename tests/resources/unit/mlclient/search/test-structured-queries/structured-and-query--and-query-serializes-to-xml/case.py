"""Test AndQuery through the public structured-query API."""

from tests.utils.resources import read_query_expectation
from xml.etree import ElementTree
from mlclient.search.structured import AndQuery, TermQuery


def run():
    query = AndQuery([TermQuery("blue"), TermQuery("green")], ordered=True)
    expected = ElementTree.fromstring(
        read_query_expectation(__file__, "expected-1.xml"),
    )[0]
    assert ElementTree.tostring(query.to_xml()) == ElementTree.tostring(expected)
