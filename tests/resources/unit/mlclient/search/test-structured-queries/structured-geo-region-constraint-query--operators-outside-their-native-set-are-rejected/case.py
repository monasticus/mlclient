import pytest
from mlclient.search.structured import GeoRegionConstraintQuery, Point
from tests.utils.resources import read_query_expectation


def run():
    with pytest.raises(ValueError, match="is not a") as error:
        GeoRegionConstraintQuery("region", Point(10, 20), operator="bogus")
    assert str(error.value) == read_query_expectation(__file__, "error.json")["message"]
