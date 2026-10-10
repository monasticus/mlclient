"""Public compilation and native serialization of SimilarQuery."""

from mlclient.xquery import FunctionCall, SimilarQuery, cts


def run():
    query = cts.similar_query(
        FunctionCall("xdmp:unquote", ("<report>blue</report>",)),
        weight=2,
    )
    assert isinstance(query, SimilarQuery)
    assert query.compile() == (
        (
            'xquery version "1.0-ml";\ndeclare variable $v0 as xs:str'
            "ing external;\ndeclare variable $v1 as xs:integer extern"
            "al;\ncts:similar-query(xdmp:unquote($v0), xs:double($v1)"
            ")"
        ),
        {"v0": "<report>blue</report>", "v1": "2"},
    )
