"""Test RangeQuery through the public structured-query API."""

from xml.etree import ElementTree
from mlclient.search.structured import PathIndex, RangeQuery


def run():
    query = RangeQuery(PathIndex("/report/price"), 2, operator="LT")
    expected = ElementTree.fromstring(
        '<range-query xmlns="http://marklogic.com/appservices/se'
        'arch"><path-index>/report/price</path-index><value>2</v'
        "alue><range-operator>LT</range-operator></range-query>",
    )
    assert ElementTree.tostring(query.to_xml()) == ElementTree.tostring(expected)
