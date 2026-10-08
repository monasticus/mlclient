"""Native ``cts:element-value-query`` serialization through the public CTS builder."""

from xml.etree.ElementTree import tostring

from mlclient.xquery import ElementValueQuery, cts


def test_element_value_query():
    query = cts.element_value_query("title", "blue")
    assert isinstance(query, ElementValueQuery)
    assert query.serialize() == {
        "elementValueQuery": {"element": ["title"], "text": ["blue"]},
    }
    assert tostring(query.to_xml(), encoding="unicode") == (
        '<cts:element-value-query xmlns:cts="http://marklogic.com/cts">'
        "<cts:element>title</cts:element><cts:text>blue</cts:text>"
        "</cts:element-value-query>"
    )


def test_element_value_query_any_value():
    query = cts.element_value_query("title")
    assert isinstance(query, ElementValueQuery)
    assert query.serialize() == {
        "elementValueQuery": {"element": ["title"], "text": ["*"]},
    }
    assert tostring(query.to_xml(), encoding="unicode") == (
        '<cts:element-value-query xmlns:cts="http://marklogic.com/cts">'
        "<cts:element>title</cts:element><cts:text>*</cts:text>"
        "</cts:element-value-query>"
    )
