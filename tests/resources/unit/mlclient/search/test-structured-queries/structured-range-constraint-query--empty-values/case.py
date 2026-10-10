import pytest
from mlclient.search.structured import RangeConstraintQuery


def run():
    with pytest.raises(ValueError, match=r""".+""") as exc:
        RangeConstraintQuery("price", []).serialize("xml")
    assert str(exc.value) == "Range queries require at least one value."
