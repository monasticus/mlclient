"""Arguments that CTS queries cannot serialize locally are rejected explicitly."""

import json
import pytest
from mlclient.xquery import FunctionCall, cts


def run():
    query = cts.reverse_query(FunctionCall("xdmp:unquote", ("{not json",)))
    with pytest.raises(
        ValueError,
        match=r"""^cts:reverse-query: nodes: Expecting""",
    ) as error:
        query.to_json()
    argument_error = error.value.__cause__
    assert isinstance(argument_error.__cause__, json.JSONDecodeError)
