"""Runtime CTS queries compile but cannot be described without evaluation."""

from mlclient.xquery import RuntimeQuery, cts


def run():
    query = cts.parse("blue AND green")
    assert isinstance(query, RuntimeQuery)
    assert query.compile() == (
        (
            'xquery version "1.0-ml";\ndeclare variable $v0 as xs:str'
            "ing external;\ncts:parse($v0)"
        ),
        {"v0": "blue AND green"},
    )
