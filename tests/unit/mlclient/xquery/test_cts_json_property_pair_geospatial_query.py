"""Serialization through the public CTS builder.

Native constructor: ``cts:json-property-pair-geospatial-query``.
"""

from xml.etree.ElementTree import tostring

from mlclient.xquery import JsonPropertyPairGeospatialQuery, cts


def test_json_property_pair_geospatial_query():
    query = cts.json_property_pair_geospatial_query(
        "location",
        "lat",
        "lon",
        cts.point(10, 20),
    )
    assert isinstance(query, JsonPropertyPairGeospatialQuery)
    assert query.serialize() == {
        "jsonPropertyPairGeospatialQuery": {
            "property": ["location"],
            "latitude": ["lat"],
            "longitude": ["lon"],
            "region": ["10,20"],
        },
    }
    assert tostring(query.to_xml(), encoding="unicode") == (
        '<cts:json-property-pair-geospatial-query xmlns:cts="http://marklogic.com'
        '/cts" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
        "<cts:property>location</cts:property><cts:latitude>lat</cts:latitude>"
        "<cts:longitude>lon</cts:longitude>"
        '<cts:region xmlns:cts="http://marklogic.com/cts" xsi:type="cts:point">10'
        ",20"
        "</cts:region></cts:json-property-pair-geospatial-query>"
    )
