"""Runtime CTS queries compile but cannot be described without evaluation."""

from mlclient.xquery import FunctionCall, cts


def run():
    query = cts.parse("blue", bindings=FunctionCall("map:map"))
    assert query.compile() == (
        (
            'xquery version "1.0-ml";\ndeclare variable $v0 as xs:str'
            "ing external;\ncts:parse($v0, map:map())"
        ),
        {"v0": "blue"},
    )
