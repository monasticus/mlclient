"""Test TermQuery through the public structured-query API."""

from decimal import Decimal
import pytest
from mlclient.search.structured import TermQuery


@pytest.mark.parametrize("weight", [Decimal("NaN"), Decimal("Infinity"), float("-inf")])
def run(weight):
    with pytest.raises(ValueError, match="must be finite") as exc:
        TermQuery("blue", weight=weight)
    assert str(exc.value) == "TermQuery.weight must be finite."
