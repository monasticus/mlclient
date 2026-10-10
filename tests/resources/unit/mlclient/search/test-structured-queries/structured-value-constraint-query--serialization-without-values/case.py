from xml.etree import ElementTree
from mlclient.search.structured import ValueConstraintQuery


def run():
    query = ValueConstraintQuery("status")
    expected = ElementTree.fromstring(
        '<value-constraint-query xmlns="http://marklogic.com/app'
        'services/search"><constraint-name>status</constraint-na'
        "me></value-constraint-query>",
    )
    assert ElementTree.tostring(query.to_xml()) == ElementTree.tostring(expected)
