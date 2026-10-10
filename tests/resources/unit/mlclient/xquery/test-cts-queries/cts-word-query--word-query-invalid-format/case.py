"""Native word-query serialization through the public CTS builder."""

import pytest
from mlclient.xquery import cts


def run():
    with pytest.raises(ValueError, match="Query format must be json or xml") as error:
        cts.word_query("blue").serialize("yaml")
    assert str(error.value) == "cts:word-query: Query format must be json or xml."
