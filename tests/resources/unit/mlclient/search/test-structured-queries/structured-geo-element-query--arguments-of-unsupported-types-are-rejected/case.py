import pytest
from mlclient.search.structured import GeoElementQuery, Point
from tests.utils.resources import read_query_expectation


def run():
    with pytest.raises(TypeError) as error:
        GeoElementQuery("location", Point(10, 20))
    assert str(error.value) == read_query_expectation(__file__, "error.json")["message"]
