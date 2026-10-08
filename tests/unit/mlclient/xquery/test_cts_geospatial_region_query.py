"""Public compilation and native serialization of GeospatialRegionQuery."""

from xml.etree.ElementTree import tostring


from mlclient.xquery import GeospatialRegionQuery, cts


def test_reference_extra_arguments():
    query = cts.geospatial_region_query(
        cts.geospatial_region_path_reference(
            "/report/region",
            options=["unchecked", "coordinate-system=wgs84"],
            geohash_precision=4,
            units="km",
            invalid_values="reject",
        ),
        "intersects",
        cts.box(1, 2, 3, 4),
    )
    assert query.serialize() == {
        "geospatialRegionQuery": {
            "geospatialRegionPathReference": [
                {
                    "geospatialRegionPathReference": {
                        "pathExpression": "/report/region",
                        "coordinateSystem": "wgs84",
                        "geohashPrecision": "4",
                        "units": "km",
                        "invalidValues": "reject",
                    },
                },
            ],
            "operation": "intersects",
            "region": ["[1, 2, 3, 4]"],
        },
    }
    assert tostring(query.to_xml(), encoding="unicode") == (
        '<cts:geospatial-region-query xmlns:cts="http://marklogic.com/cts" '
        'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
        "<cts:geospatial-region-path-reference><cts:path-expression>"
        "/report/region</cts:path-expression><cts:coordinate-system>wgs84"
        "</cts:coordinate-system><cts:geohash-precision>4</cts:geohash-precision>"
        "<cts:units>km</cts:units><cts:invalid-values>reject</cts:invalid-values>"
        "</cts:geospatial-region-path-reference><cts:operation>intersects"
        '</cts:operation><cts:region xmlns:cts="http://marklogic.com/cts" '
        'xsi:type="cts:box">[1, 2, 3, 4]</cts:region></cts:geospatial-region-query>'
    )


def test_compilation():
    query = cts.geospatial_region_query(
        cts.geospatial_region_path_reference(
            "/report/region",
            options=["unchecked", "coordinate-system=wgs84"],
        ),
        "intersects",
        cts.box(1, 2, 3, 4),
        options="cached",
        weight=2,
    )
    assert isinstance(query, GeospatialRegionQuery)
    assert query.compile() == (
        (
            'xquery version "1.0-ml";\ndeclare variable $v0 as xs:string exte'
            "rnal;\ndeclare variable $v1 as xs:string external;\ndeclare vari"
            "able $v2 as xs:string external;\ndeclare variable $v3 as xs:stri"
            "ng external;\ndeclare variable $v4 as xs:integer external;\ndecl"
            "are variable $v5 as xs:integer external;\ndeclare variable $v6 a"
            "s xs:integer external;\ndeclare variable $v7 as xs:integer exter"
            "nal;\ndeclare variable $v8 as xs:string external;\ndeclare varia"
            "ble $v9 as xs:integer external;\ncts:geospatial-region-query(cts"
            ":geospatial-region-path-reference($v0, ($v1, $v2)), $v3, cts:box"
            "(xs:double($v4), xs:double($v5), xs:double($v6), xs:double($v7)), $v"
            "8, xs:double($v9))"
        ),
        {
            "v0": "/report/region",
            "v1": "unchecked",
            "v2": "coordinate-system=wgs84",
            "v3": "intersects",
            "v4": "1",
            "v5": "2",
            "v6": "3",
            "v7": "4",
            "v8": "cached",
            "v9": "2",
        },
    )


def test_serialization():
    query = cts.geospatial_region_query(
        cts.geospatial_region_path_reference(
            "/report/region",
            options=["unchecked", "coordinate-system=wgs84"],
        ),
        "intersects",
        cts.box(1, 2, 3, 4),
        options="cached",
        weight=2,
    )
    expected = {
        "geospatialRegionQuery": {
            "geospatialRegionPathReference": [
                {
                    "geospatialRegionPathReference": {
                        "pathExpression": "/report/region",
                        "coordinateSystem": "wgs84",
                    },
                },
            ],
            "operation": "intersects",
            "region": ["[1, 2, 3, 4]"],
            "options": ["cached"],
            "weight": 2,
        },
    }
    assert query.serialize() == expected
    assert query.to_json() == expected
    assert query.to_combined_query() == {"search": {"ctsquery": expected}}
    assert tostring(query.serialize("xml"), encoding="unicode") == (
        '<cts:geospatial-region-query xmlns:cts="http://marklogic.com/cts'
        '" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" weight="'
        '2"><cts:geospatial-region-path-reference><cts:path-expression>/r'
        "eport/region</cts:path-expression><cts:coordinate-system>wgs84</"
        "cts:coordinate-system></cts:geospatial-region-path-reference><cts:"
        'operation>intersects</cts:operation><cts:region xmlns:cts="htt'
        'p://marklogic.com/cts" xsi:type="cts:box">[1, 2, 3, 4]</cts:regi'
        "on><cts:option>cached</cts:option></cts:geospatial-region-query>"
    )
