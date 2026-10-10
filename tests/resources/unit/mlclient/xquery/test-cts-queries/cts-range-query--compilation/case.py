"""Public compilation and native serialization of RangeQuery."""

from mlclient.xquery import RangeQuery, cts


def run():
    query = cts.range_query(
        cts.element_reference("price", options=["type=int", "unchecked"]),
        ">=",
        [2, 3],
        options="cached",
        weight=2,
    )
    assert isinstance(query, RangeQuery)
    assert query.compile() == (
        (
            'xquery version "1.0-ml";\ndeclare variable $v0 as xs:str'
            "ing external;\ndeclare variable $v1 as xs:string externa"
            "l;\ndeclare variable $v2 as xs:string external;\ndeclare "
            "variable $v3 as xs:string external;\ndeclare variable $v"
            "4 as xs:integer external;\ndeclare variable $v5 as xs:in"
            "teger external;\ndeclare variable $v6 as xs:string exter"
            "nal;\ndeclare variable $v7 as xs:integer external;\ncts:r"
            "ange-query(cts:element-reference(xs:QName($v0), ($v1, $"
            "v2)), xs:string($v3), ($v4, $v5), $v6, xs:double($v7))"
        ),
        {
            "v0": "price",
            "v1": "type=int",
            "v2": "unchecked",
            "v3": ">=",
            "v4": "2",
            "v5": "3",
            "v6": "cached",
            "v7": "2",
        },
    )
