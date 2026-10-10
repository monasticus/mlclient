"""Arguments that CTS queries cannot serialize locally are rejected explicitly."""

import pytest
from mlclient.xquery import cts


def run():
    with pytest.raises(TypeError) as error:
        cts.element_word_query("t:title", "blue").serialize()
    assert str(error.value) == (
        "cts:element-word-query: element: Prefixed CTS QNames re"
        "quire compilation namespace bindings; use fn.qname(uri,"
        " name) for local serialization."
    )
