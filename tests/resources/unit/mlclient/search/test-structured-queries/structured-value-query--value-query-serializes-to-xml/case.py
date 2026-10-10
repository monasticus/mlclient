"""Test ValueQuery through the public structured-query API."""

from tests.utils.resources import read_query_expectation
from xml.etree import ElementTree
from mlclient.search.structured import JsonProperty, ValueQuery


def run():
    query = ValueQuery(
        JsonProperty("active"),
        True,
        node_type="boolean",
        options=["exact"],
        weight=2,
        fragment_scope="documents",
    )
    expected = ElementTree.fromstring(
        read_query_expectation(__file__, "expected-1.xml"),
    )[0]
    assert ElementTree.tostring(query.to_xml()) == ElementTree.tostring(expected)
