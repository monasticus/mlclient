"""Public compilation and native serialization of RangeQuery."""

import pytest
from mlclient.xquery import cts


def run():
    reference = cts.element_reference("price", options="type=int").pos(1)
    with pytest.raises(TypeError) as error:
        cts.range_query(reference, "=", 2).serialize()
    assert str(error.value) == (
        "cts:range-query: reference: CTS reference argument requ"
        "ires server evaluation, got Index(inner=FunctionCall(fn"
        "='cts:element-reference', args=(FunctionCall(fn='xs:QNa"
        "me', args=(AtomicValue(value='price', cast=None),), opt"
        "ionals=()),), optionals=(AtomicValue(value='type=int', "
        "cast=None),)), position=1)."
    )
