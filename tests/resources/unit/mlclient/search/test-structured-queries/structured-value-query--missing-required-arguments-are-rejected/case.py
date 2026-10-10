import pytest
from mlclient.search.structured import JsonProperty, ValueQuery
from tests.utils.resources import read_query_expectation


def run():
    with pytest.raises(TypeError) as error:
        ValueQuery(JsonProperty("count"), None)
    assert str(error.value) == read_query_expectation(__file__, "error.json")["message"]
