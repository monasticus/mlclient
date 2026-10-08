"""Serialization through the public CTS builder.

Native constructor: ``cts:element-attribute-pair-geospatial-query``.
"""

from xml.etree.ElementTree import tostring

from mlclient.xquery import ElementAttributePairGeospatialQuery, cts


def test_element_attribute_pair_geospatial_query():
    query = cts.element_attribute_pair_geospatial_query(
        "item",
        "lat",
        "lon",
        cts.point(10, 20),
        weight=3,
    )
    assert isinstance(query, ElementAttributePairGeospatialQuery)
    assert query.serialize() == {
        "elementAttributePairGeospatialQuery": {
            "element": ["item"],
            "latitudeAttribute": ["lat"],
            "longitudeAttribute": ["lon"],
            "region": ["10,20"],
            "weight": 3.0,
        },
    }
    assert tostring(query.to_xml(), encoding="unicode") == (
        '<cts:element-attribute-pair-geospatial-query xmlns:cts="http://marklogic'
        '.com/cts" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" weight="'
        '3">'
        "<cts:element>item</cts:element><cts:latitude>lat</cts:latitude>"
        "<cts:longitude>lon</cts:longitude>"
        '<cts:region xmlns:cts="http://marklogic.com/cts" xsi:type="cts:point">10'
        ",20"
        "</cts:region></cts:element-attribute-pair-geospatial-query>"
    )
