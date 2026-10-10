"""Arguments that CTS queries cannot serialize locally are rejected explicitly."""

import pytest
from mlclient.xquery import cts, fn


def run():
    query = cts.and_query(
        [cts.word_query("blue"), cts.not_query(cts.word_query(fn.string("x")))],
    )
    with pytest.raises(TypeError) as error:
        query.to_xml()
    assert str(error.value) == (
        "cts:and-query: queries: cts:not-query: query: cts:word-"
        "query: text: CTS string argument requires server evalua"
        "tion, got fn:string('x')."
    )
