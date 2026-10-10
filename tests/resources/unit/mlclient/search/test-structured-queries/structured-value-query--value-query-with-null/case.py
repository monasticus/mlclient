"""Test ValueQuery through the public structured-query API."""

from xml.etree import ElementTree
from mlclient.search.structured import JsonProperty, ValueQuery


def run():
    query = ValueQuery(JsonProperty("count"), "", node_type="null")
    expected = ElementTree.fromstring(
        '<value-query xmlns="http://marklogic.com/appservices/se'
        'arch" type="null"><json-property>count</json-property><'
        "text /></value-query>",
    )
    assert ElementTree.tostring(query.to_xml()) == ElementTree.tostring(expected)
