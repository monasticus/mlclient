"""Native ``cts:field-value-query`` serialization through the public CTS builder."""

from xml.etree.ElementTree import tostring

from mlclient.xquery import FieldValueQuery, cts


def test_field_value_query():
    query = cts.field_value_query("price", ["1", "2"], weight=3)
    assert isinstance(query, FieldValueQuery)
    assert query.serialize() == {
        "fieldValueQuery": {"field": ["price"], "text": ["1", "2"], "weight": 3.0},
    }
    assert tostring(query.to_xml(), encoding="unicode") == (
        '<cts:field-value-query xmlns:cts="http://marklogic.com/cts" weight="3">'
        "<cts:field>price</cts:field><cts:text>1</cts:text><cts:text>2</cts:text>"
        "</cts:field-value-query>"
    )
