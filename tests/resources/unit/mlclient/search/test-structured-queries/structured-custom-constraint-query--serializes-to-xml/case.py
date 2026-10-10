"""Test custom-constraint-query serialization."""

from xml.etree import ElementTree
from mlclient.search.structured import CustomConstraintQuery


def run():
    query = CustomConstraintQuery("custom", ["blue", "green"])
    expected = ElementTree.fromstring(
        '<custom-constraint-query xmlns="http://marklogic.com/ap'
        'pservices/search"><constraint-name>custom</constraint-n'
        "ame><text>blue</text><text>green</text></custom-constra"
        "int-query>",
    )
    assert ElementTree.tostring(query.to_xml()) == ElementTree.tostring(expected)
