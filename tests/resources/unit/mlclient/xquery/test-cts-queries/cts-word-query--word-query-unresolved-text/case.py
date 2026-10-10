"""Native word-query serialization through the public CTS builder."""

import pytest
from mlclient.xquery import cts, fn


def run():
    with pytest.raises(TypeError) as error:
        cts.word_query(fn.string("blue")).serialize()
    assert str(error.value) == (
        "cts:word-query: text: CTS string argument requires serv"
        "er evaluation, got fn:string('blue')."
    )
