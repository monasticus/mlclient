"""Test RangeQuery through the public structured-query API."""

from tests.utils.resources import read_query_expectation
from xml.etree import ElementTree
from mlclient.search.structured import Attribute, Element, RangeQuery


def run():
    query = RangeQuery(
        Element("price"),
        [3, 4],
        operator="EQ",
        index_type="xs:int",
        collation="urn:example",
        options=["cached"],
        weight=2,
        fragment_scope="documents",
        attribute=Attribute("amount"),
    )
    expected = ElementTree.fromstring(
        read_query_expectation(__file__, "expected-1.xml"),
    )[0]
    assert ElementTree.tostring(query.to_xml()) == ElementTree.tostring(expected)
