"""Runtime CTS queries compile but cannot be described without evaluation."""

from mlclient.xquery import cts


def run():
    query = cts.and_query([cts.parse("blue"), cts.collection_query("reports")])
    assert query.compile() == (
        (
            'xquery version "1.0-ml";\ndeclare variable $v0 as xs:str'
            "ing external;\ndeclare variable $v1 as xs:string externa"
            "l;\ncts:and-query((cts:parse($v0), cts:collection-query("
            "$v1)))"
        ),
        {"v0": "blue", "v1": "reports"},
    )
