"""Serialization through the public CTS builder.

Native constructor: ``cts:json-property-child-geospatial-query``.
"""

from xml.etree.ElementTree import tostring

from mlclient.xquery import JsonPropertyChildGeospatialQuery, cts


def test_json_property_child_geospatial_query():
    query = cts.json_property_child_geospatial_query(
        "location",
        "point",
        cts.point(10, 20),
    )
    assert isinstance(query, JsonPropertyChildGeospatialQuery)
    assert query.serialize() == {
        "jsonPropertyChildGeospatialQuery": {
            "property": ["location"],
            "child": ["point"],
            "region": ["10,20"],
        },
    }
    assert tostring(query.to_xml(), encoding="unicode") == (
        '<cts:json-property-child-geospatial-query xmlns:cts="http://marklogic.co'
        'm/cts" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
        "<cts:property>location</cts:property><cts:child>point</cts:child>"
        '<cts:region xmlns:cts="http://marklogic.com/cts" xsi:type="cts:point">10'
        ",20"
        "</cts:region></cts:json-property-child-geospatial-query>"
    )
