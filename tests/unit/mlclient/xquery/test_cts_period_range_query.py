"""Native ``cts:period-range-query`` serialization through the public CTS builder."""

import datetime
from xml.etree.ElementTree import tostring

from mlclient.xquery import PeriodRangeQuery, cts

START = datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc)
END = datetime.datetime(2026, 2, 1, tzinfo=datetime.timezone.utc)


def test_period_range_query():
    query = cts.period_range_query(
        ["valid", "system"],
        "aln_before",
        period=cts.period(START, END),
    )
    assert isinstance(query, PeriodRangeQuery)
    assert query.serialize() == {
        "periodRangeQuery": {
            "axis": ["valid", "system"],
            "operator": "aln_before",
            "period": [
                {
                    "periodStart": "2026-01-01T00:00:00+00:00",
                    "periodEnd": "2026-02-01T00:00:00+00:00",
                },
            ],
        },
    }
    assert tostring(query.to_xml(), encoding="unicode") == (
        '<cts:period-range-query xmlns:cts="http://marklogic.com/cts" operator="a'
        'ln_before">'
        "<cts:axis>valid</cts:axis><cts:axis>system</cts:axis><cts:period>"
        "<cts:period-start>2026-01-01T00:00:00+00:00</cts:period-start>"
        "<cts:period-end>2026-02-01T00:00:00+00:00</cts:period-end></cts:period>"
        "</cts:period-range-query>"
    )


def test_period_range_query_without_period():
    query = cts.period_range_query("valid", "aln_before")
    assert isinstance(query, PeriodRangeQuery)
    assert query.serialize() == {
        "periodRangeQuery": {"axis": ["valid"], "operator": "aln_before"},
    }
    assert tostring(query.to_xml(), encoding="unicode") == (
        '<cts:period-range-query xmlns:cts="http://marklogic.com/cts" operator="a'
        'ln_before">'
        "<cts:axis>valid</cts:axis></cts:period-range-query>"
    )
