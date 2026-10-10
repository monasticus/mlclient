import pytest
from mlclient.search.structured import PeriodRangeQuery
from tests.utils.resources import read_query_expectation


def run():
    with pytest.raises(TypeError) as error:
        PeriodRangeQuery("valid", "aln_equals", "2024")
    assert str(error.value) == read_query_expectation(__file__, "error.json")["message"]
