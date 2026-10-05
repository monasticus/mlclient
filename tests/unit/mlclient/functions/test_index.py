import pytest

from mlclient.functions.xqy import Cts, Index, fn


@pytest.mark.parametrize("position", [True, 1.5, "1", fn.count([])])
def test_index_rejects_non_positions(position):
    with pytest.raises(TypeError) as error:
        Index(Cts.uris(), position)

    assert str(error.value) == "index/range positions must be integers or fn.last()"


def test_last_stays_inside_index_predicate():
    expression = Cts.uris().pos(pos=fn.last())
    code, variables = expression.compile()

    assert code == ('xquery version "1.0-ml";\ncts:uris()[fn:last()]')
    assert variables == {}


def test_index_rejects_zero():
    with pytest.raises(
        ValueError,
        match=r"^index/range positions must be positive$",
    ) as error:
        Cts.uris().pos(0)

    assert str(error.value) == "index/range positions must be positive"
