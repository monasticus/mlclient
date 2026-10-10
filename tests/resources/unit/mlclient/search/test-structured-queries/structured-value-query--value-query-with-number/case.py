"""Test ValueQuery through the public structured-query API."""

from xml.etree import ElementTree
from mlclient.search.structured import JsonProperty, ValueQuery


def run():
    query = ValueQuery(JsonProperty("count"), 7, node_type="number")
    expected = ElementTree.fromstring(
        '<value-query xmlns="http://marklogic.com/appservices/se'
        'arch" type="number"><json-property>count</json-property'
        "><text>7</text></value-query>",
    )
    assert ElementTree.tostring(query.to_xml()) == ElementTree.tostring(expected)
