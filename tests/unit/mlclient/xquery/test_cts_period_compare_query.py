"""Native ``cts:period-compare-query`` serialization through the public CTS builder."""

from xml.etree.ElementTree import tostring

from mlclient.xquery import PeriodCompareQuery, cts


def test_period_compare_query():
    query = cts.period_compare_query(
        "system",
        "aln_equals",
        "valid",
        options="cached-incremental",
    )
    assert isinstance(query, PeriodCompareQuery)
    assert query.serialize() == {
        "periodCompareQuery": {
            "axis1": "system",
            "operator": "aln_equals",
            "axis2": "valid",
            "options": ["cached-incremental"],
        },
    }
    assert tostring(query.to_xml(), encoding="unicode") == (
        '<cts:period-compare-query xmlns:cts="http://marklogic.com/cts" operator='
        '"aln_equals">'
        "<cts:axis1>system</cts:axis1><cts:axis2>valid</cts:axis2>"
        "<cts:option>cached-incremental</cts:option></cts:period-compare-query>"
    )
