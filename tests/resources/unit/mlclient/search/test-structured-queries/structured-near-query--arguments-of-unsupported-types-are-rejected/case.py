import pytest
from mlclient.search.structured import NearQuery, TermQuery
from tests.utils.resources import read_query_expectation


def run():
    with pytest.raises(TypeError) as error:
        NearQuery([TermQuery("a")], distance=1.5)
    assert str(error.value) == read_query_expectation(__file__, "error.json")["message"]
