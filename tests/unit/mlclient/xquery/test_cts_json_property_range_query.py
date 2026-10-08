"""Serialization through the public CTS builder.

Native constructor: ``cts:json-property-range-query``.
"""

from xml.etree.ElementTree import tostring

from mlclient.xquery import JsonPropertyRangeQuery, cts


def test_json_property_range_query():
    query = cts.json_property_range_query("price", ">", 10)
    assert isinstance(query, JsonPropertyRangeQuery)
    assert query.serialize() == {
        "jsonPropertyRangeQuery": {
            "property": ["price"],
            "operator": ">",
            "value": [{"type": "decimal", "val": "10"}],
        },
    }
    assert tostring(query.to_xml(), encoding="unicode") == (
        '<cts:json-property-range-query xmlns:cts="http://marklogic.com/cts" xmln'
        's:xsi="http://www.w3.org/2001/XMLSchema-instance" operator="&gt;">'
        "<cts:property>price</cts:property>"
        '<cts:value xmlns:xs="http://www.w3.org/2001/XMLSchema" xsi:type="xs:inte'
        'ger">10'
        "</cts:value></cts:json-property-range-query>"
    )
