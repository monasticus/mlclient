"""Native ``cts:before-query`` serialization through the public CTS builder."""

from xml.etree.ElementTree import tostring

from mlclient.xquery import BeforeQuery, cts


def test_before_query():
    query = cts.before_query(16000000000)
    assert isinstance(query, BeforeQuery)
    assert query.serialize() == {"beforeQuery": {"timestamp": "16000000000"}}
    assert tostring(query.to_xml(), encoding="unicode") == (
        '<cts:before-query xmlns:cts="http://marklogic.com/cts">'
        "<cts:timestamp>16000000000</cts:timestamp></cts:before-query>"
    )
