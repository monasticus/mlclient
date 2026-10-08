"""Serialization through the public CTS builder.

Native constructor: ``cts:json-property-geospatial-query``.
"""

from xml.etree.ElementTree import tostring

from mlclient.xquery import JsonPropertyGeospatialQuery, cts


def test_json_property_geospatial_query():
    query = cts.json_property_geospatial_query("origin", cts.point(10, 20))
    assert isinstance(query, JsonPropertyGeospatialQuery)
    assert query.serialize() == {
        "jsonPropertyGeospatialQuery": {"property": ["origin"], "region": ["10,20"]},
    }
    assert tostring(query.to_xml(), encoding="unicode") == (
        '<cts:json-property-geospatial-query xmlns:cts="http://marklogic.com/cts"'
        ' xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
        "<cts:property>origin</cts:property>"
        '<cts:region xmlns:cts="http://marklogic.com/cts" xsi:type="cts:point">10'
        ",20"
        "</cts:region></cts:json-property-geospatial-query>"
    )
