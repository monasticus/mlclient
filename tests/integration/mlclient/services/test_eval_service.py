import pytest

from mlclient.xquery import fn


pytestmark = pytest.mark.ml_access


def test_expression(indexed_database):
    ml, database, _ = indexed_database

    result = ml.eval.expression(fn.upper_case("works"), database=database)

    assert result == "WORKS"
