"""Test collection-constraint-query serialization."""

from xml.etree import ElementTree
from mlclient.search.structured import CollectionConstraintQuery


def run():
    query = CollectionConstraintQuery("category", ["blue", "green"])
    expected = ElementTree.fromstring(
        '<collection-constraint-query xmlns="http://marklogic.co'
        'm/appservices/search"><constraint-name>category</constr'
        "aint-name><uri>blue</uri><uri>green</uri></collection-c"
        "onstraint-query>",
    )
    assert ElementTree.tostring(query.to_xml()) == ElementTree.tostring(expected)
