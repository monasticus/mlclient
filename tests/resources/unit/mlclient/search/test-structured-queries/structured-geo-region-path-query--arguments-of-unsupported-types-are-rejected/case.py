import pytest
from mlclient.search.structured import GeoRegionPathQuery, Point
from tests.utils.resources import read_query_expectation


def run():
    with pytest.raises(TypeError) as error:
        GeoRegionPathQuery("/region", Point(10, 20))
    assert str(error.value) == read_query_expectation(__file__, "error.json")["message"]
