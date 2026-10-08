from xml.etree import ElementTree

from mlclient.search.structured import ValueConstraintQuery


def test_serialization_text_json():
    query = ValueConstraintQuery("status", ["blue", "green"], weight=2)
    expected = {
        "value-constraint-query": {
            "constraint-name": "status",
            "text": ["blue", "green"],
            "weight": 2,
        },
    }
    assert query.serialize() == expected
    assert query.serialize("json") == expected


def test_serialization_text():
    query = ValueConstraintQuery("status", ["blue", "green"], weight=2)
    expected = ElementTree.fromstring(
        '<value-constraint-query xmlns="http://marklogic.com/appservices/search">'
        "<constraint-name>status</constraint-name><text>blue</text><text>green</text>"
        "<weight>2</weight></value-constraint-query>",
    )
    assert ElementTree.tostring(query.to_xml()) == ElementTree.tostring(expected)


def test_serialization_number():
    query = ValueConstraintQuery("count", 7)
    expected = ElementTree.fromstring(
        '<value-constraint-query xmlns="http://marklogic.com/appservices/search">'
        "<constraint-name>count</constraint-name><text>7</text>"
        "</value-constraint-query>",
    )
    assert ElementTree.tostring(query.to_xml()) == ElementTree.tostring(expected)


def test_serialization_boolean():
    query = ValueConstraintQuery("active", False)
    expected = ElementTree.fromstring(
        '<value-constraint-query xmlns="http://marklogic.com/appservices/search">'
        "<constraint-name>active</constraint-name><text>false</text>"
        "</value-constraint-query>",
    )
    assert ElementTree.tostring(query.to_xml()) == ElementTree.tostring(expected)


def test_serialization_without_values():
    query = ValueConstraintQuery("status")
    expected = ElementTree.fromstring(
        '<value-constraint-query xmlns="http://marklogic.com/appservices/search">'
        "<constraint-name>status</constraint-name></value-constraint-query>",
    )
    assert ElementTree.tostring(query.to_xml()) == ElementTree.tostring(expected)
