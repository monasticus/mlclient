"""Native ``cts:element-word-query`` serialization through the public CTS builder."""

from xml.etree.ElementTree import tostring

from mlclient.xquery import ElementWordQuery, cts, fn

NS = "urn:mlclient:cts-test"


def test_element_word_query():
    query = cts.element_word_query(
        fn.qname(NS, "title"),
        ["blue", "red"],
        options="case-insensitive",
        weight=2,
    )
    assert isinstance(query, ElementWordQuery)
    assert query.serialize() == {
        "elementWordQuery": {
            "element": ["{urn:mlclient:cts-test}title"],
            "text": ["blue", "red"],
            "options": ["case-insensitive"],
            "weight": 2.0,
        },
    }
    assert tostring(query.to_xml(), encoding="unicode") == (
        '<cts:element-word-query xmlns:cts="http://marklogic.com/cts" weight="2">'
        '<cts:element xmlns:q="urn:mlclient:cts-test">q:title</cts:element>'
        "<cts:text>blue</cts:text><cts:text>red</cts:text>"
        "<cts:option>case-insensitive</cts:option></cts:element-word-query>"
    )
