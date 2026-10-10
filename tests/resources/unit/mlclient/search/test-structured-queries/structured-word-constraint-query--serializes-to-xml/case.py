"""Test word-constraint-query serialization."""

from xml.etree import ElementTree
from mlclient.search.structured import WordConstraintQuery


def run():
    query = WordConstraintQuery("title", ["blue", "green"], weight=2)
    expected = ElementTree.fromstring(
        '<word-constraint-query xmlns="http://marklogic.com/apps'
        'ervices/search"><constraint-name>title</constraint-name'
        "><text>blue</text><text>green</text><weight>2</weight><"
        "/word-constraint-query>",
    )
    assert ElementTree.tostring(query.to_xml()) == ElementTree.tostring(expected)
