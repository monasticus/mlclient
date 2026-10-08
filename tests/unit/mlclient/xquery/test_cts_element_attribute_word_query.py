"""Serialization through the public CTS builder.

Native constructor: ``cts:element-attribute-word-query``.
"""

from xml.etree.ElementTree import tostring

from mlclient.xquery import ElementAttributeWordQuery, cts


def test_element_attribute_word_query():
    query = cts.element_attribute_word_query("item", "status", "ok")
    assert isinstance(query, ElementAttributeWordQuery)
    assert query.serialize() == {
        "elementAttributeWordQuery": {
            "element": ["item"],
            "attribute": ["status"],
            "text": ["ok"],
        },
    }
    assert tostring(query.to_xml(), encoding="unicode") == (
        '<cts:element-attribute-word-query xmlns:cts="http://marklogic.com/cts">'
        "<cts:element>item</cts:element><cts:attribute>status</cts:attribute>"
        "<cts:text>ok</cts:text></cts:element-attribute-word-query>"
    )
