from xml.etree import ElementTree
from mlclient.search.structured import ValueConstraintQuery


def run():
    query = ValueConstraintQuery("count", 7)
    expected = ElementTree.fromstring(
        '<value-constraint-query xmlns="http://marklogic.com/app'
        'services/search"><constraint-name>count</constraint-nam'
        "e><text>7</text></value-constraint-query>",
    )
    assert ElementTree.tostring(query.to_xml()) == ElementTree.tostring(expected)
