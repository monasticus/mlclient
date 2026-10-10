"""Public compilation and native serialization of RangeQuery."""

import pytest
from mlclient.xquery import FunctionCall, cts


def run():
    with pytest.raises(TypeError) as error:
        cts.range_query(
            FunctionCall("cts:reference-parse", ("reference",)),
            "=",
            2,
        ).serialize()
    assert str(error.value) == (
        "cts:range-query: reference: CTS reference argument requ"
        "ires server evaluation, got cts:reference-parse('refere"
        "nce')."
    )
