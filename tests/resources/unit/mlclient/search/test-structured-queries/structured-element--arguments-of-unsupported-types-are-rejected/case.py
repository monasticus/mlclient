import pytest
from mlclient.search.structured import Element
from tests.utils.resources import read_query_expectation


def run():
    with pytest.raises(TypeError) as error:
        Element(5)
    assert str(error.value) == read_query_expectation(__file__, "error.json")["message"]
