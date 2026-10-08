"""Native ``cts:after-query`` serialization through the public CTS builder."""

from xml.etree.ElementTree import tostring

from mlclient.xquery import AfterQuery, cts


def test_after_query():
    query = cts.after_query(16000000000)
    assert isinstance(query, AfterQuery)
    assert query.serialize() == {"afterQuery": {"timestamp": "16000000000"}}
    assert tostring(query.to_xml(), encoding="unicode") == (
        '<cts:after-query xmlns:cts="http://marklogic.com/cts">'
        "<cts:timestamp>16000000000</cts:timestamp></cts:after-query>"
    )
