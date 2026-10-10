import pytest
from mlclient.search.structured import Period, PeriodRangeQuery
from tests.utils.resources import read_query_expectation


def run():
    with pytest.raises(ValueError, match="is not a") as error:
        PeriodRangeQuery(
            "valid", "bogus", Period("2026-01-01T00:00:00Z", "2026-02-01T00:00:00Z"),
        )
    assert str(error.value) == read_query_expectation(__file__, "error.json")["message"]
