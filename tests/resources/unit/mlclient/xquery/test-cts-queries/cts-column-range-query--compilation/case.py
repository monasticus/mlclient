"""Public compilation and native serialization of ColumnRangeQuery."""

from mlclient.xquery import ColumnRangeQuery, cts


def run():
    query = cts.column_range_query(
        "reports",
        "items",
        "price",
        2,
        operator=">=",
        options="cached",
        weight=2,
    )
    assert isinstance(query, ColumnRangeQuery)
    assert query.compile() == (
        (
            'xquery version "1.0-ml";\ndeclare variable $v0 as xs:str'
            "ing external;\ndeclare variable $v1 as xs:string externa"
            "l;\ndeclare variable $v2 as xs:string external;\ndeclare "
            "variable $v3 as xs:integer external;\ndeclare variable $"
            "v4 as xs:string external;\ndeclare variable $v5 as xs:st"
            "ring external;\ndeclare variable $v6 as xs:integer exter"
            "nal;\ncts:column-range-query($v0, $v1, $v2, $v3, xs:stri"
            "ng($v4), $v5, xs:double($v6))"
        ),
        {
            "v0": "reports",
            "v1": "items",
            "v2": "price",
            "v3": "2",
            "v4": ">=",
            "v5": "cached",
            "v6": "2",
        },
    )
