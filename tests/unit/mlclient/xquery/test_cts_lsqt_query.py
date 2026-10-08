"""Native ``cts:lsqt-query`` serialization through the public CTS builder."""

import datetime
from xml.etree.ElementTree import tostring

from mlclient.xquery import LsqtQuery, cts

START = datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc)


def test_lsqt_query():
    query = cts.lsqt_query("temporal", timestamp=START, options="cached", weight=2)
    assert isinstance(query, LsqtQuery)
    assert query.serialize() == {
        "lsqtQuery": {
            "temporalCollection": "temporal",
            "timestamp": "2026-01-01T00:00:00+00:00",
            "options": ["cached"],
            "weight": 2.0,
        },
    }
    assert tostring(query.to_xml(), encoding="unicode") == (
        '<cts:lsqt-query xmlns:cts="http://marklogic.com/cts" weight="2">'
        "<cts:temporal-collection>temporal</cts:temporal-collection>"
        "<cts:timestamp>2026-01-01T00:00:00+00:00</cts:timestamp>"
        "<cts:option>cached</cts:option></cts:lsqt-query>"
    )


def test_lsqt_query_defaults():
    query = cts.lsqt_query("temporal")
    assert isinstance(query, LsqtQuery)
    assert query.serialize() == {"lsqtQuery": {"temporalCollection": "temporal"}}
    assert tostring(query.to_xml(), encoding="unicode") == (
        '<cts:lsqt-query xmlns:cts="http://marklogic.com/cts">'
        "<cts:temporal-collection>temporal</cts:temporal-collection>"
        "</cts:lsqt-query>"
    )
