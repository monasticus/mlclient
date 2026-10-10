"""Public compilation and native serialization of ReverseQuery."""

import pytest
from mlclient.xquery import FunctionCall, cts


def run():
    query = cts.reverse_query(
        FunctionCall("xdmp:unquote", ("<!DOCTYPE report><report/>",)),
    )
    with pytest.raises(TypeError) as error:
        query.serialize()
    assert str(error.value) == (
        "cts:reverse-query: nodes: CTS literal XML with a DTD re"
        "quires server evaluation."
    )
