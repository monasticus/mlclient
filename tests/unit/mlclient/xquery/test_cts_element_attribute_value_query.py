"""Serialization through the public CTS builder.

Native constructor: ``cts:element-attribute-value-query``.
"""

from xml.etree.ElementTree import tostring

from mlclient.xquery import ElementAttributeValueQuery, cts


def test_element_attribute_value_query():
    query = cts.element_attribute_value_query(
        "item",
        "status",
        "ok",
        options="exact",
        weight=0.5,
    )
    assert isinstance(query, ElementAttributeValueQuery)
    assert query.serialize() == {
        "elementAttributeValueQuery": {
            "element": ["item"],
            "attribute": ["status"],
            "text": ["ok"],
            "options": ["exact"],
            "weight": 0.5,
        },
    }
    assert tostring(query.to_xml(), encoding="unicode") == (
        '<cts:element-attribute-value-query xmlns:cts="http://marklogic.com/cts" '
        'weight="0.5">'
        "<cts:element>item</cts:element><cts:attribute>status</cts:attribute>"
        "<cts:text>ok</cts:text><cts:option>exact</cts:option>"
        "</cts:element-attribute-value-query>"
    )
