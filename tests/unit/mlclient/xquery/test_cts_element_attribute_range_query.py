"""Serialization through the public CTS builder.

Native constructor: ``cts:element-attribute-range-query``.
"""

from xml.etree.ElementTree import tostring

from mlclient.xquery import ElementAttributeRangeQuery, cts


def test_element_attribute_range_query():
    query = cts.element_attribute_range_query("item", "amount", "!=", 3)
    assert isinstance(query, ElementAttributeRangeQuery)
    assert query.serialize() == {
        "elementAttributeRangeQuery": {
            "element": ["item"],
            "attribute": ["amount"],
            "operator": "!=",
            "value": [{"type": "decimal", "val": "3"}],
        },
    }
    assert tostring(query.to_xml(), encoding="unicode") == (
        '<cts:element-attribute-range-query xmlns:cts="http://marklogic.com/cts" '
        'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" operator="!=">'
        "<cts:element>item</cts:element><cts:attribute>amount</cts:attribute>"
        '<cts:value xmlns:xs="http://www.w3.org/2001/XMLSchema" xsi:type="xs:inte'
        'ger">3'
        "</cts:value></cts:element-attribute-range-query>"
    )
