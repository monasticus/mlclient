"""Public compilation and native serialization of GeospatialRegionQuery."""

from mlclient.xquery import GeospatialRegionQuery, cts


def run():
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
            'xquery version "1.0-ml";\ndeclare variable $v0 as xs:str'
            "ing external;\ndeclare variable $v1 as xs:string externa"
            "l;\ndeclare variable $v2 as xs:string external;\ndeclare "
            "variable $v3 as xs:string external;\ndeclare variable $v"
            "4 as xs:integer external;\ndeclare variable $v5 as xs:in"
            "teger external;\ndeclare variable $v6 as xs:integer exte"
            "rnal;\ndeclare variable $v7 as xs:integer external;\ndecl"
            "are variable $v8 as xs:string external;\ndeclare variabl"
            "e $v9 as xs:integer external;\ncts:geospatial-region-que"
            "ry(cts:geospatial-region-path-reference($v0, ($v1, $v2)"
            "), $v3, cts:box(xs:double($v4), xs:double($v5), xs:doub"
            "le($v6), xs:double($v7)), $v8, xs:double($v9))"
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
