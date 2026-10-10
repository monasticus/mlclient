"""Native word-query serialization through the public CTS builder."""

import pytest
from mlclient.xquery import FunctionCall, cts


def run():
    with pytest.raises(TypeError) as error:
        cts.word_query("blue", weight=FunctionCall("xs:double", (2, 3))).serialize()
    assert str(error.value) == (
        "cts:word-query: weight: CTS numeric argument requires s"
        "erver evaluation, got xs:double(2, 3)."
    )
