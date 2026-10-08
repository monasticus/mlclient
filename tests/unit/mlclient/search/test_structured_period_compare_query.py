"""Test PeriodCompareQuery through its public API."""

from xml.etree import ElementTree

from mlclient.search.structured import PeriodCompareQuery


def test_serializes_to_json():
    query = PeriodCompareQuery("system", "aln_equals", "valid", options=["cached"])
    expected = {
        "period-compare-query": {
            "axis1": "system",
            "temporal-operator": "aln_equals",
            "axis2": "valid",
            "temporal-option": ["cached"],
        },
    }
    assert query.serialize() == expected
    assert query.serialize("json") == expected


def test_serializes_to_xml():
    query = PeriodCompareQuery("system", "aln_equals", "valid", options=["cached"])
    expected = ElementTree.fromstring(
        '<expected xmlns="http://marklogic.com/appservices/search">'
        "<period-compare-query>"
        "<axis1>system"
        "</axis1>"
        "<temporal-operator>aln_equals"
        "</temporal-operator>"
        "<axis2>valid"
        "</axis2>"
        "<temporal-option>cached"
        "</temporal-option>"
        "</period-compare-query>"
        "</expected>",
    )[0]
    assert ElementTree.tostring(query.to_xml()) == ElementTree.tostring(expected)
