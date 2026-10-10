"""Native word-query serialization through the public CTS builder."""

import pytest
from mlclient.xquery import cts, fn


def run():
    with pytest.raises(TypeError) as error:
        cts.word_query("blue", weight=fn.last()).serialize()
    assert str(error.value) == (
        "cts:word-query: weight: CTS numeric argument requires s"
        "erver evaluation, got fn:last()."
    )
