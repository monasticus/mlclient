from __future__ import annotations

from decimal import Decimal

import pytest

from mlclient.functions.xqy import cts, fn, xs


@pytest.mark.parametrize("value", [Decimal("NaN"), Decimal("Infinity")])
def test_nonfinite_decimals_are_rejected(value):
    with pytest.raises(ValueError, match="finite"):
        xs.decimal(value)


@pytest.mark.parametrize(
    ("expr", "native", "value"),
    [
        (xs.integer("1"), "xs:integer", "1"),
        (xs.double("1.25"), "xs:double", "1.25"),
        (xs.decimal("1.25"), "xs:decimal", "1.25"),
        (xs.string("coffee"), "xs:string", "coffee"),
        (xs.qname("item"), "xs:QName", "item"),
        (xs.date("2026-01-01"), "xs:date", "2026-01-01"),
        (xs.date_time("2026-01-01T00:00:00"), "xs:dateTime", "2026-01-01T00:00:00"),
    ],
)
def test_compile_type_constructor(expr, native, value):
    assert expr.compile() == (
        'xquery version "1.0-ml";\n'
        "declare variable $v0 as xs:string external;\n"
        f"{native}($v0)",
        {"v0": value},
    )


def test_cast_preserves_the_composed_expression():
    assert xs.string(
        fn.count(cts.values(cts.element_reference("price"))),
    ).compile() == (
        'xquery version "1.0-ml";\n'
        "declare variable $v0 as xs:string external;\n"
        "xs:string(fn:count(cts:values(cts:element-reference(xs:QName($v0)))))",
        {"v0": "price"},
    )
