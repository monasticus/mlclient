import pytest

from mlclient.functions.xqy import Cts, fn


@pytest.mark.parametrize(
    ("start", "end", "error_type", "message"),
    [
        (True, 2, TypeError, "index/range positions must be integers or fn.last()"),
        (1, False, TypeError, "index/range positions must be integers or fn.last()"),
        (1.5, 2, TypeError, "index/range positions must be integers or fn.last()"),
        (1, "2", TypeError, "index/range positions must be integers or fn.last()"),
        (0, 1, ValueError, "index/range positions must be positive"),
        (3, 2, ValueError, "range bounds must satisfy 1 <= start <= end"),
    ],
)
def test_range_rejects_invalid_positions(start, end, error_type, message):
    with pytest.raises(error_type) as error:
        Cts.search().pos([start, end])

    assert str(error.value) == message


def test_range_composes_inside_count():
    expression = fn.count(Cts.search(query=Cts.false_query()).pos([2, 5]))
    code, variables = expression.compile()

    assert code == (
        'xquery version "1.0-ml";\n'
        "declare variable $v0 as xs:integer external;\n"
        "declare variable $v1 as xs:integer external;\n"
        "fn:count(cts:search(/, cts:false-query())[$v0 to $v1])"
    )
    assert variables == {"v0": "2", "v1": "5"}


def test_last_stays_inside_range_end():
    expression = Cts.uris().pos([1, fn.last()])
    code, variables = expression.compile()

    assert code == (
        'xquery version "1.0-ml";\n'
        "declare variable $v0 as xs:integer external;\n"
        "cts:uris()[$v0 to fn:last()]"
    )
    assert variables == {"v0": "1"}


def test_last_stays_inside_both_range_bounds():
    expression = Cts.uris().pos([fn.last(), fn.last()])
    code, variables = expression.compile()

    assert code == ('xquery version "1.0-ml";\ncts:uris()[fn:last() to fn:last()]')
    assert variables == {}
