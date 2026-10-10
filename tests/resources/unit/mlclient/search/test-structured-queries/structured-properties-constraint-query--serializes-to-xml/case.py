"""Test properties-constraint-query serialization."""

from xml.etree import ElementTree
from mlclient.search.structured import PropertiesConstraintQuery, TrueQuery


def run():
    query = PropertiesConstraintQuery("metadata", TrueQuery())
    expected = ElementTree.fromstring(
        '<properties-constraint-query xmlns="http://marklogic.co'
        'm/appservices/search"><constraint-name>metadata</constr'
        "aint-name><true-query /></properties-constraint-query>",
    )
    assert ElementTree.tostring(query.to_xml()) == ElementTree.tostring(expected)
