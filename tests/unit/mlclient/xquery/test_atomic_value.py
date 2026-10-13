from __future__ import annotations

import json
from datetime import date, datetime, timezone
from decimal import Decimal

import pytest

from mlclient.xquery import fn


def test_values_are_json_safe_and_keep_precision():
    expression = fn.count(
        [
            True,
            2**80,
            Decimal("1.234567890123456789"),
            date(2026, 1, 2),
            datetime(2026, 1, 2, tzinfo=timezone.utc),
            float("inf"),
            float("-inf"),
            float("nan"),
            1.25,
        ],
    )
    code, variables = expression.compile()

    assert code == (
        'xquery version "1.0-ml";\n'
        "declare variable $v0 as xs:boolean external;\n"
        "declare variable $v1 as xs:integer external;\n"
        "declare variable $v2 as xs:decimal external;\n"
        "declare variable $v3 as xs:date external;\n"
        "declare variable $v4 as xs:dateTime external;\n"
        "declare variable $v5 as xs:double external;\n"
        "declare variable $v6 as xs:double external;\n"
        "declare variable $v7 as xs:double external;\n"
        "declare variable $v8 as xs:double external;\n"
        "fn:count(($v0, $v1, $v2, $v3, $v4, $v5, $v6, $v7, $v8))"
    )
    assert variables == {
        "v0": True,
        "v1": "1208925819614629174706176",
        "v2": "1.234567890123456789",
        "v3": "2026-01-02",
        "v4": "2026-01-02T00:00:00+00:00",
        "v5": "INF",
        "v6": "-INF",
        "v7": "NaN",
        "v8": "1.25",
    }

    assert json.loads(json.dumps(variables)) == variables


@pytest.mark.parametrize(
    ("value", "message"),
    [
        ({1}, "unsupported XQuery value type: set"),
        (iter([1]), "unsupported XQuery value type: list_iterator"),
        (object(), "unsupported XQuery value type: object"),
    ],
)
def test_unsupported_values_are_rejected_when_building(value, message):
    with pytest.raises(TypeError) as error:
        fn.count(value)

    assert str(error.value) == message


def test_nonfinite_decimal_is_rejected():
    with pytest.raises(
        ValueError,
        match=r"^xs:decimal requires a finite Decimal$",
    ) as error:
        fn.count(Decimal("NaN"))

    assert str(error.value) == "xs:decimal requires a finite Decimal"
