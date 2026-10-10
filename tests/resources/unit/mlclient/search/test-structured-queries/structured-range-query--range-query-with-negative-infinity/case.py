"""Test RangeQuery through the public structured-query API."""

from xml.etree import ElementTree
from mlclient.search.structured import Element, RangeQuery


def run():
    query = RangeQuery(Element("price"), float("-inf"), index_type="xs:double")
    expected = ElementTree.fromstring(
        '<range-query xmlns="http://marklogic.com/appservices/se'
        'arch" type="xs:double"><element name="price" ns="" /><v'
        "alue>-INF</value></range-query>",
    )
    assert ElementTree.tostring(query.to_xml()) == ElementTree.tostring(expected)
