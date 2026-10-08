"""Serialization through the public CTS builder.

Native constructor: ``cts:element-geospatial-query``.
"""

from xml.etree.ElementTree import tostring

from mlclient.xquery import ElementGeospatialQuery, cts


def test_element_geospatial_query_point():
    query = cts.element_geospatial_query(
        "origin",
        cts.point(10.5, -20.25),
        options="coordinate-system=wgs84",
        weight=2,
    )
    assert isinstance(query, ElementGeospatialQuery)
    assert query.serialize() == {
        "elementGeospatialQuery": {
            "element": ["origin"],
            "region": ["10.5,-20.25"],
            "options": ["coordinate-system=wgs84"],
            "weight": 2.0,
        },
    }
    assert tostring(query.to_xml(), encoding="unicode") == (
        '<cts:element-geospatial-query xmlns:cts="http://marklogic.com/cts" xmlns'
        ':xsi="http://www.w3.org/2001/XMLSchema-instance" weight="2">'
        "<cts:element>origin</cts:element>"
        '<cts:region xmlns:cts="http://marklogic.com/cts" xsi:type="cts:point">10'
        ".5,-20.25"
        "</cts:region><cts:option>coordinate-system=wgs84</cts:option>"
        "</cts:element-geospatial-query>"
    )


def test_element_geospatial_query_regions():
    query = cts.element_geospatial_query(
        "origin",
        [
            cts.box(1.5, 2, 3, 4),
            cts.circle(5, cts.point(10, 20)),
            cts.polygon(
                [cts.point(0, 0), cts.point(0, 1), cts.point(1, 1), cts.point(0, 0)],
            ),
        ],
    )
    assert isinstance(query, ElementGeospatialQuery)
    assert query.serialize() == {
        "elementGeospatialQuery": {
            "element": ["origin"],
            "region": ["[1.5, 2, 3, 4]", "@5 10,20", "0,0 0,1 1,1 0,0"],
        },
    }
    assert tostring(query.to_xml(), encoding="unicode") == (
        '<cts:element-geospatial-query xmlns:cts="http://marklogic.com/cts" xmlns'
        ':xsi="http://www.w3.org/2001/XMLSchema-instance">'
        "<cts:element>origin</cts:element>"
        '<cts:region xmlns:cts="http://marklogic.com/cts" xsi:type="cts:box">[1.5'
        ", 2, 3, 4]"
        "</cts:region>"
        '<cts:region xmlns:cts="http://marklogic.com/cts" xsi:type="cts:circle">@'
        "5 10,20"
        "</cts:region>"
        '<cts:region xmlns:cts="http://marklogic.com/cts" xsi:type="cts:polygon">'
        "0,0 0,1 1,1 0,0"
        "</cts:region></cts:element-geospatial-query>"
    )
