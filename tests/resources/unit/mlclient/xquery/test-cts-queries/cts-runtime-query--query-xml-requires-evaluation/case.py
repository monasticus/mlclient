"""Runtime CTS queries compile but cannot be described without evaluation."""

import pytest
from mlclient.xquery import FunctionCall, cts


def run():
    with pytest.raises(TypeError) as error:
        cts.query(FunctionCall("fn:doc", ("/query.xml",))).to_xml()
    assert str(error.value) == (
        "runtime query: CTS runtime query requires server evalua"
        "tion before serialization."
    )
