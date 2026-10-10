"""Public compilation and native serialization of ReverseQuery."""

import pytest
from mlclient.xquery import cts, fn


def run():
    query = cts.reverse_query(fn.doc("/report.xml"))
    assert query.compile() == (
        (
            'xquery version "1.0-ml";\ndeclare variable $v0 as xs:str'
            "ing external;\ncts:reverse-query(fn:doc($v0))"
        ),
        {"v0": "/report.xml"},
    )
    with pytest.raises(TypeError) as error:
        query.serialize()
    assert str(error.value) == (
        "cts:reverse-query: nodes: CTS node argument requires a "
        "literal xdmp:unquote call or server evaluation."
    )
