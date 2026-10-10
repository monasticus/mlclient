import pytest
from mlclient.search.structured import Polygon
from tests.utils.resources import read_query_expectation


def run():
    with pytest.raises(TypeError) as error:
        Polygon([(1, 2), (3, 4), (1, 2)])
    assert str(error.value) == read_query_expectation(__file__, "error.json")["message"]
