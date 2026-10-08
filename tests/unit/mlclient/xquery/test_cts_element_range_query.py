"""Native ``cts:element-range-query`` serialization through the public CTS builder."""

import datetime
from decimal import Decimal
from xml.etree.ElementTree import tostring

from mlclient.xquery import ElementRangeQuery, cts, xs

START = datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc)


def test_element_range_query_integer():
    query = cts.element_range_query("price", ">=", 10, options="min-occurs=1", weight=2)
    assert isinstance(query, ElementRangeQuery)
    assert query.serialize() == {
        "elementRangeQuery": {
            "element": ["price"],
            "operator": ">=",
            "value": [{"type": "decimal", "val": "10"}],
            "options": ["min-occurs=1"],
            "weight": 2.0,
        },
    }
    assert tostring(query.to_xml(), encoding="unicode") == (
        '<cts:element-range-query xmlns:cts="http://marklogic.com/cts" xmlns:xsi='
        '"http://www.w3.org/2001/XMLSchema-instance" operator="&gt;=" weight="2">'
        "<cts:element>price</cts:element>"
        '<cts:value xmlns:xs="http://www.w3.org/2001/XMLSchema" xsi:type="xs:inte'
        'ger">10'
        "</cts:value><cts:option>min-occurs=1</cts:option>"
        "</cts:element-range-query>"
    )


def test_element_range_query_decimal():
    query = cts.element_range_query("price", "<", Decimal("1.5"))
    assert isinstance(query, ElementRangeQuery)
    assert query.serialize() == {
        "elementRangeQuery": {
            "element": ["price"],
            "operator": "<",
            "value": [{"type": "decimal", "val": "1.5"}],
        },
    }
    assert tostring(query.to_xml(), encoding="unicode") == (
        '<cts:element-range-query xmlns:cts="http://marklogic.com/cts" xmlns:xsi='
        '"http://www.w3.org/2001/XMLSchema-instance" operator="&lt;">'
        "<cts:element>price</cts:element>"
        '<cts:value xmlns:xs="http://www.w3.org/2001/XMLSchema" xsi:type="xs:deci'
        'mal">1.5'
        "</cts:value></cts:element-range-query>"
    )


def test_element_range_query_double():
    query = cts.element_range_query("price", ">", xs.double(1.5))
    assert isinstance(query, ElementRangeQuery)
    assert query.serialize() == {
        "elementRangeQuery": {
            "element": ["price"],
            "operator": ">",
            "value": [{"type": "double", "val": "1.5"}],
        },
    }
    assert tostring(query.to_xml(), encoding="unicode") == (
        '<cts:element-range-query xmlns:cts="http://marklogic.com/cts" xmlns:xsi='
        '"http://www.w3.org/2001/XMLSchema-instance" operator="&gt;">'
        "<cts:element>price</cts:element>"
        '<cts:value xmlns:xs="http://www.w3.org/2001/XMLSchema" xsi:type="xs:doub'
        'le">1.5'
        "</cts:value></cts:element-range-query>"
    )


def test_element_range_query_strings():
    query = cts.element_range_query("code", "=", ["a", "b"])
    assert isinstance(query, ElementRangeQuery)
    assert query.serialize() == {
        "elementRangeQuery": {
            "element": ["code"],
            "operator": "=",
            "value": [{"type": "string", "val": "a"}, {"type": "string", "val": "b"}],
        },
    }
    assert tostring(query.to_xml(), encoding="unicode") == (
        '<cts:element-range-query xmlns:cts="http://marklogic.com/cts" xmlns:xsi='
        '"http://www.w3.org/2001/XMLSchema-instance" operator="=">'
        "<cts:element>code</cts:element>"
        '<cts:value xmlns:xs="http://www.w3.org/2001/XMLSchema" xsi:type="xs:stri'
        'ng">a'
        "</cts:value>"
        '<cts:value xmlns:xs="http://www.w3.org/2001/XMLSchema" xsi:type="xs:stri'
        'ng">b'
        "</cts:value></cts:element-range-query>"
    )


def test_element_range_query_date():
    query = cts.element_range_query("day", ">", datetime.date(2026, 1, 1))
    assert isinstance(query, ElementRangeQuery)
    assert query.serialize() == {
        "elementRangeQuery": {
            "element": ["day"],
            "operator": ">",
            "value": [{"type": "date", "val": "2026-01-01"}],
        },
    }
    assert tostring(query.to_xml(), encoding="unicode") == (
        '<cts:element-range-query xmlns:cts="http://marklogic.com/cts" xmlns:xsi='
        '"http://www.w3.org/2001/XMLSchema-instance" operator="&gt;">'
        "<cts:element>day</cts:element>"
        '<cts:value xmlns:xs="http://www.w3.org/2001/XMLSchema" xsi:type="xs:date'
        '">2026-01-01'
        "</cts:value></cts:element-range-query>"
    )


def test_element_range_query_date_time():
    query = cts.element_range_query("at", "<=", START)
    assert isinstance(query, ElementRangeQuery)
    assert query.serialize() == {
        "elementRangeQuery": {
            "element": ["at"],
            "operator": "<=",
            "value": [{"type": "dateTime", "val": "2026-01-01T00:00:00+00:00"}],
        },
    }
    assert tostring(query.to_xml(), encoding="unicode") == (
        '<cts:element-range-query xmlns:cts="http://marklogic.com/cts" xmlns:xsi='
        '"http://www.w3.org/2001/XMLSchema-instance" operator="&lt;=">'
        "<cts:element>at</cts:element>"
        '<cts:value xmlns:xs="http://www.w3.org/2001/XMLSchema" xsi:type="xs:date'
        'Time">2026-01-01T00:00:00+00:00'
        "</cts:value></cts:element-range-query>"
    )


def test_element_range_query_boolean():
    query = cts.element_range_query("flag", "=", True)
    assert isinstance(query, ElementRangeQuery)
    assert query.serialize() == {
        "elementRangeQuery": {
            "element": ["flag"],
            "operator": "=",
            "value": [{"type": "boolean", "val": "true"}],
        },
    }
    assert tostring(query.to_xml(), encoding="unicode") == (
        '<cts:element-range-query xmlns:cts="http://marklogic.com/cts" xmlns:xsi='
        '"http://www.w3.org/2001/XMLSchema-instance" operator="=">'
        "<cts:element>flag</cts:element>"
        '<cts:value xmlns:xs="http://www.w3.org/2001/XMLSchema" xsi:type="xs:bool'
        'ean">true'
        "</cts:value></cts:element-range-query>"
    )
