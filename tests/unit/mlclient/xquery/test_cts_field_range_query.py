"""Native ``cts:field-range-query`` serialization through the public CTS builder."""

from xml.etree.ElementTree import tostring

from mlclient.xquery import FieldRangeQuery, cts


def test_field_range_query():
    query = cts.field_range_query("price", "<=", 2)
    assert isinstance(query, FieldRangeQuery)
    assert query.serialize() == {
        "fieldRangeQuery": {
            "field": ["price"],
            "operator": "<=",
            "value": [{"type": "decimal", "val": "2"}],
        },
    }
    assert tostring(query.to_xml(), encoding="unicode") == (
        '<cts:field-range-query xmlns:cts="http://marklogic.com/cts" xmlns:xsi="h'
        'ttp://www.w3.org/2001/XMLSchema-instance" operator="&lt;=">'
        "<cts:field>price</cts:field>"
        '<cts:value xmlns:xs="http://www.w3.org/2001/XMLSchema" xsi:type="xs:inte'
        'ger">2'
        "</cts:value></cts:field-range-query>"
    )
