import pytest
from mlclient.search.structured import PeriodCompareQuery
from tests.utils.resources import read_query_expectation


def run():
    with pytest.raises(ValueError, match="is not a") as error:
        PeriodCompareQuery("system", "bogus", "valid")
    assert str(error.value) == read_query_expectation(__file__, "error.json")["message"]
