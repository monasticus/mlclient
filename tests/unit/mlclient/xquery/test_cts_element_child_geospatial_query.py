"""Serialization through the public CTS builder.

Native constructor: ``cts:element-child-geospatial-query``.
"""

from xml.etree.ElementTree import tostring

from mlclient.xquery import ElementChildGeospatialQuery, cts


def test_element_child_geospatial_query():
    query = cts.element_child_geospatial_query("location", "point", cts.point(10, 20))
    assert isinstance(query, ElementChildGeospatialQuery)
    assert query.serialize() == {
        "elementChildGeospatialQuery": {
            "element": ["location"],
            "child": ["point"],
            "region": ["10,20"],
        },
    }
    assert tostring(query.to_xml(), encoding="unicode") == (
        '<cts:element-child-geospatial-query xmlns:cts="http://marklogic.com/cts"'
        ' xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
        "<cts:element>location</cts:element><cts:child>point</cts:child>"
        '<cts:region xmlns:cts="http://marklogic.com/cts" xsi:type="cts:point">10'
        ",20"
        "</cts:region></cts:element-child-geospatial-query>"
    )
