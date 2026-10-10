import pytest
from mlclient.search.structured import Period
from tests.utils.resources import read_query_expectation


def run():
    with pytest.raises(TypeError) as error:
        Period("2026-01-01T00:00:00Z", None)
    assert str(error.value) == read_query_expectation(__file__, "error.json")["message"]
