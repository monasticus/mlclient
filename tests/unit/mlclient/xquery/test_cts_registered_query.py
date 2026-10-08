"""Native ``cts:registered-query`` serialization through the public CTS builder."""

from xml.etree.ElementTree import tostring

from mlclient.xquery import RegisteredQuery, cts


def test_registered_query():
    query = cts.registered_query([1, 2], options="unfiltered", weight=2)
    assert isinstance(query, RegisteredQuery)
    assert query.serialize() == {
        "registeredQuery": {
            "ids": ["1", "2"],
            "options": ["unfiltered"],
            "weight": 2.0,
        },
    }
    assert tostring(query.to_xml(), encoding="unicode") == (
        '<cts:registered-query xmlns:cts="http://marklogic.com/cts" weight="2">'
        "<cts:id>1</cts:id><cts:id>2</cts:id><cts:option>unfiltered</cts:option>"
        "</cts:registered-query>"
    )
