"""Test PeriodRangeQuery through its public API."""

from xml.etree import ElementTree

from mlclient.search.structured import Period, PeriodRangeQuery


def test_serializes_to_json():
    query = PeriodRangeQuery(
        ["valid", "system"],
        "aln_contains",
        [Period("2024-01-01T00:00:00Z", "2025-01-01T00:00:00Z")],
        options=["cached"],
        weight=2,
    )
    expected = {
        "period-range-query": {
            "axis": ["valid", "system"],
            "temporal-operator": "aln_contains",
            "period": [
                {
                    "period-start": "2024-01-01T00:00:00Z",
                    "period-end": "2025-01-01T00:00:00Z",
                },
            ],
            "temporal-option": ["cached"],
            "weight": 2,
        },
    }
    assert query.serialize() == expected
    assert query.serialize("json") == expected


def test_serializes_to_xml():
    query = PeriodRangeQuery(
        ["valid", "system"],
        "aln_contains",
        [Period("2024-01-01T00:00:00Z", "2025-01-01T00:00:00Z")],
        options=["cached"],
        weight=2,
    )
    expected = ElementTree.fromstring(
        '<expected xmlns="http://marklogic.com/appservices/search">'
        "<period-range-query>"
        "<axis>valid"
        "</axis>"
        "<axis>system"
        "</axis>"
        "<temporal-operator>aln_contains"
        "</temporal-operator>"
        "<period>"
        "<period-start>2024-01-01T00:00:00Z"
        "</period-start>"
        "<period-end>2025-01-01T00:00:00Z"
        "</period-end>"
        "</period>"
        "<temporal-option>cached"
        "</temporal-option>"
        "<weight>2"
        "</weight>"
        "</period-range-query>"
        "</expected>",
    )[0]
    assert ElementTree.tostring(query.to_xml()) == ElementTree.tostring(expected)
