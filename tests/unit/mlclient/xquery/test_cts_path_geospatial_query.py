"""Native ``cts:path-geospatial-query`` serialization through the public CTS builder."""

from xml.etree.ElementTree import tostring

from mlclient.xquery import PathGeospatialQuery, cts


def test_path_geospatial_query():
    query = cts.path_geospatial_query("/item/origin", cts.point(10, 20))
    assert isinstance(query, PathGeospatialQuery)
    assert query.serialize() == {
        "pathGeospatialQuery": {
            "pathExpression": ["/item/origin"],
            "region": ["10,20"],
        },
    }
    assert tostring(query.to_xml(), encoding="unicode") == (
        '<cts:path-geospatial-query xmlns:cts="http://marklogic.com/cts" xmlns:xs'
        'i="http://www.w3.org/2001/XMLSchema-instance">'
        "<cts:path-expression>/item/origin</cts:path-expression>"
        '<cts:region xmlns:cts="http://marklogic.com/cts" xsi:type="cts:point">10'
        ",20"
        "</cts:region></cts:path-geospatial-query>"
    )
