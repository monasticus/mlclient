from xml.etree import ElementTree
from mlclient.search.structured import RangeConstraintQuery


def run():
    query = RangeConstraintQuery("price", [3, 4], operator="EQ", options=["cached"])
    expected = ElementTree.fromstring(
        '<range-constraint-query xmlns="http://marklogic.com/app'
        'services/search"><constraint-name>price</constraint-nam'
        "e><value>3</value><value>4</value><range-operator>EQ</r"
        "ange-operator><range-option>cached</range-option></rang"
        "e-constraint-query>",
    )
    assert ElementTree.tostring(query.to_xml()) == ElementTree.tostring(expected)
