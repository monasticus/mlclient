import pytest
from mlclient.search.structured import RangeConstraintQuery


def run():
    with pytest.raises(ValueError, match=r""".+""") as exc:
        RangeConstraintQuery("price", 3, operator="INVALID").serialize("xml")
    assert str(exc.value) == "Range operator must be LT, LE, GT, GE, EQ, or NE."
