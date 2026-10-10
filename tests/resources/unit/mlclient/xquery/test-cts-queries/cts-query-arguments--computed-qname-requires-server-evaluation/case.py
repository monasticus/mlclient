"""Arguments that CTS queries cannot serialize locally are rejected explicitly."""

import pytest
from mlclient.xquery import cts, fn


def run():
    with pytest.raises(TypeError) as error:
        cts.element_word_query(fn.node_name(fn.doc("/a.xml")), "blue").serialize()
    assert str(error.value) == (
        "cts:element-word-query: element: CTS QName argument req"
        "uires server evaluation, got fn:node-name(fn:doc('/a.xm"
        "l'))."
    )
