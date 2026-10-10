import pytest
from mlclient.search.structured import RangeConstraintQuery


def run():
    with pytest.raises(ValueError, match=r""".+""") as exc:
        RangeConstraintQuery("price", [3, 4], operator="GT").serialize("xml")
    assert str(exc.value) == "Multiple range values require EQ or NE."
