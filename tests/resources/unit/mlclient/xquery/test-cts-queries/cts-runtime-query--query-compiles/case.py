"""Runtime CTS queries compile but cannot be described without evaluation."""

from mlclient.xquery import FunctionCall, RuntimeQuery, cts


def run():
    source = '{"wordQuery":{"text":["blue"]}}'
    query = cts.query(FunctionCall("xdmp:unquote", (source,)))
    assert isinstance(query, RuntimeQuery)
    assert query.compile() == (
        (
            'xquery version "1.0-ml";\ndeclare variable $v0 as xs:str'
            "ing external;\ncts:query(xdmp:unquote($v0))"
        ),
        {"v0": source},
    )
