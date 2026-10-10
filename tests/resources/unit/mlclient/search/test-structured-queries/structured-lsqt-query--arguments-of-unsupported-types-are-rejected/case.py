import pytest
from mlclient.search.structured import LsqtQuery
from tests.utils.resources import read_query_expectation


def run():
    with pytest.raises(TypeError) as error:
        LsqtQuery(5)
    assert str(error.value) == read_query_expectation(__file__, "error.json")["message"]
