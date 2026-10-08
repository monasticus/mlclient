from decimal import Decimal

from mlclient.models import TupleHit


def test_tuple_values_and_frequency():
    values = (Decimal("1.25"), True)
    hit = TupleHit(values, frequency=2)

    assert hit.values is values
    assert hit.frequency == 2
