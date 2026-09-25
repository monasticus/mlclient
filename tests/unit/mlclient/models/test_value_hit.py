from datetime import date
from decimal import Decimal

import pytest

from mlclient.models import ValueHit


@pytest.mark.parametrize("value", ["word", 7, Decimal("1.25"), date(2026, 1, 2)])
def test_value_is_retained_without_conversion(value):
    hit = ValueHit(value, frequency=3)
    assert hit.value is value
    assert hit.frequency == 3
