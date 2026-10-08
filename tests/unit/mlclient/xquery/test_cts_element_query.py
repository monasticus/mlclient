"""Native ``cts:element-query`` serialization through the public CTS builder."""

from xml.etree.ElementTree import tostring

from mlclient.xquery import ElementQuery, cts, fn

NS = "urn:mlclient:cts-test"


def test_element_query():
    query = cts.element_query(["a", fn.qname(NS, "t:b")], cts.word_query("x"))
    assert isinstance(query, ElementQuery)
    assert query.serialize() == {
        "elementQuery": {
            "element": ["a", "{urn:mlclient:cts-test}b"],
            "query": {"wordQuery": {"text": ["x"]}},
        },
    }
    assert tostring(query.to_xml(), encoding="unicode") == (
        '<cts:element-query xmlns:cts="http://marklogic.com/cts"><cts:element>a'
        '</cts:element><cts:element xmlns:q="urn:mlclient:cts-test">q:b'
        "</cts:element><cts:word-query><cts:text>x</cts:text></cts:word-query>"
        "</cts:element-query>"
    )
