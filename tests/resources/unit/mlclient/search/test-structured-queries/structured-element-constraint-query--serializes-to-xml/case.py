"""Test element-constraint-query serialization."""

from xml.etree import ElementTree
from mlclient.search.structured import ElementConstraintQuery, TrueQuery


def run():
    query = ElementConstraintQuery("section", TrueQuery())
    expected = ElementTree.fromstring(
        '<element-constraint-query xmlns="http://marklogic.com/a'
        'ppservices/search"><constraint-name>section</constraint'
        "-name><true-query /></element-constraint-query>",
    )
    assert ElementTree.tostring(query.to_xml()) == ElementTree.tostring(expected)
