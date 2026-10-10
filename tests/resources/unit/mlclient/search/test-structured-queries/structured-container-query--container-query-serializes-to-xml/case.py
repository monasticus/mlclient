"""Test ContainerQuery through the public structured-query API."""

from tests.utils.resources import read_query_expectation
from xml.etree import ElementTree
from mlclient.search.structured import ContainerQuery, Element, TermQuery


def run():
    query = ContainerQuery(
        Element("section", "urn:example"),
        TermQuery("blue"),
        fragment_scope="properties",
    )
    expected = ElementTree.fromstring(
        read_query_expectation(__file__, "expected-1.xml"),
    )[0]
    assert ElementTree.tostring(query.to_xml()) == ElementTree.tostring(expected)
