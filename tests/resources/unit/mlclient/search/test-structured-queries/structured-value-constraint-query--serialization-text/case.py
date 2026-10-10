from xml.etree import ElementTree
from mlclient.search.structured import ValueConstraintQuery


def run():
    query = ValueConstraintQuery("status", ["blue", "green"], weight=2)
    expected = ElementTree.fromstring(
        '<value-constraint-query xmlns="http://marklogic.com/app'
        'services/search"><constraint-name>status</constraint-na'
        "me><text>blue</text><text>green</text><weight>2</weight"
        "></value-constraint-query>",
    )
    assert ElementTree.tostring(query.to_xml()) == ElementTree.tostring(expected)
