import pytest
from mlclient.search.structured import Point
from tests.utils.resources import read_query_expectation


def run():
    with pytest.raises(TypeError) as error:
        Point(None, 20)
    assert str(error.value) == read_query_expectation(__file__, "error.json")["message"]
