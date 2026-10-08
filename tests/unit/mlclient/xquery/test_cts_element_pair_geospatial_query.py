"""Serialization through the public CTS builder.

Native constructor: ``cts:element-pair-geospatial-query``.
"""

from xml.etree.ElementTree import tostring

from mlclient.xquery import ElementPairGeospatialQuery, cts


def test_element_pair_geospatial_query():
    query = cts.element_pair_geospatial_query(
        "location",
        "lat",
        "lon",
        cts.point(10, 20),
    )
    assert isinstance(query, ElementPairGeospatialQuery)
    assert query.serialize() == {
        "elementPairGeospatialQuery": {
            "element": ["location"],
            "latitude": ["lat"],
            "longitude": ["lon"],
            "region": ["10,20"],
        },
    }
    assert tostring(query.to_xml(), encoding="unicode") == (
        '<cts:element-pair-geospatial-query xmlns:cts="http://marklogic.com/cts" '
        'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
        "<cts:element>location</cts:element><cts:latitude>lat</cts:latitude>"
        "<cts:longitude>lon</cts:longitude>"
        '<cts:region xmlns:cts="http://marklogic.com/cts" xsi:type="cts:point">10'
        ",20"
        "</cts:region></cts:element-pair-geospatial-query>"
    )
