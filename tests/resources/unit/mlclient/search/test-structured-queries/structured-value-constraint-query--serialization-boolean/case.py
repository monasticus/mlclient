from xml.etree import ElementTree
from mlclient.search.structured import ValueConstraintQuery


def run():
    query = ValueConstraintQuery("active", False)
    expected = ElementTree.fromstring(
        '<value-constraint-query xmlns="http://marklogic.com/app'
        'services/search"><constraint-name>active</constraint-na'
        "me><text>false</text></value-constraint-query>",
    )
    assert ElementTree.tostring(query.to_xml()) == ElementTree.tostring(expected)
