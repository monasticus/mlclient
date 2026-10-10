"""Public compilation and native serialization of ReverseQuery."""

from mlclient.xquery import FunctionCall, ReverseQuery, cts


def run():
    query = cts.reverse_query(
        FunctionCall("xdmp:unquote", ("<report>blue</report>",)),
        weight=2,
    )
    assert isinstance(query, ReverseQuery)
    assert query.compile() == (
        (
            'xquery version "1.0-ml";\ndeclare variable $v0 as xs:str'
            "ing external;\ndeclare variable $v1 as xs:integer extern"
            "al;\ncts:reverse-query(xdmp:unquote($v0), xs:double($v1)"
            ")"
        ),
        {"v0": "<report>blue</report>", "v1": "2"},
    )
