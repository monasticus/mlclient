"""Test container-constraint-query serialization."""

from xml.etree import ElementTree
from mlclient.search.structured import ContainerConstraintQuery, TrueQuery


def run():
    query = ContainerConstraintQuery("section", TrueQuery())
    expected = ElementTree.fromstring(
        '<container-constraint-query xmlns="http://marklogic.com'
        '/appservices/search"><constraint-name>section</constrai'
        "nt-name><true-query /></container-constraint-query>",
    )
    assert ElementTree.tostring(query.to_xml()) == ElementTree.tostring(expected)
