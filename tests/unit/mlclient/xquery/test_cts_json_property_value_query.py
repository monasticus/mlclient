"""Serialization through the public CTS builder.

Native constructor: ``cts:json-property-value-query``.
"""

from xml.etree.ElementTree import tostring

from mlclient.xquery import JsonPropertyValueQuery, cts


def test_json_property_value_query_string():
    query = cts.json_property_value_query("label", "gamma")
    assert isinstance(query, JsonPropertyValueQuery)
    assert query.serialize() == {
        "jsonPropertyValueQuery": {"property": ["label"], "value": ["gamma"]},
    }
    assert tostring(query.to_xml(), encoding="unicode") == (
        '<cts:json-property-value-query xmlns:cts="http://marklogic.com/cts">'
        "<cts:property>label</cts:property><cts:value>gamma</cts:value>"
        "</cts:json-property-value-query>"
    )


def test_json_property_value_query_mixed():
    query = cts.json_property_value_query(["a", "b"], ["x", 7, 1.5, False])
    assert isinstance(query, JsonPropertyValueQuery)
    assert query.serialize() == {
        "jsonPropertyValueQuery": {
            "property": ["a", "b"],
            "value": ["x", 7, 1.5, False],
        },
    }
    assert tostring(query.to_xml(), encoding="unicode") == (
        '<cts:json-property-value-query xmlns:cts="http://marklogic.com/cts" xmln'
        's:xsi="http://www.w3.org/2001/XMLSchema-instance">'
        "<cts:property>a</cts:property><cts:property>b</cts:property><cts:value>x"
        "</cts:value>"
        '<cts:value xmlns:xs="http://www.w3.org/2001/XMLSchema" xsi:type="xs:doub'
        'le">7'
        "</cts:value>"
        '<cts:value xmlns:xs="http://www.w3.org/2001/XMLSchema" xsi:type="xs:doub'
        'le">1.5'
        "</cts:value>"
        '<cts:value xmlns:xs="http://www.w3.org/2001/XMLSchema" xsi:type="xs:bool'
        'ean">false'
        "</cts:value></cts:json-property-value-query>"
    )
