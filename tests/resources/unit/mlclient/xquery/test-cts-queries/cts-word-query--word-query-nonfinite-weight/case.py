"""Native word-query serialization through the public CTS builder."""

import pytest
from mlclient.xquery import cts


def run():
    with pytest.raises(ValueError, match="CTS numbers must be finite") as error:
        cts.word_query("blue", weight=float("inf")).serialize()
    assert (
        str(error.value)
        == "cts:word-query: weight: CTS numbers must be finite for local serialization."
    )
