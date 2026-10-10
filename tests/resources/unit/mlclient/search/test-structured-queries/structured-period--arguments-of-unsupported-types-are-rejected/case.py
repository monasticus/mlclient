from datetime import datetime
import pytest
from mlclient.search.structured import Period
from tests.utils.resources import read_query_expectation


def run():
    with pytest.raises(TypeError) as error:
        Period(datetime(2026, 1, 1), 2027)
    assert str(error.value) == read_query_expectation(__file__, "error.json")["message"]
