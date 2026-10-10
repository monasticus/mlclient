from mlclient.search.structured import sq
from tests.utils.resources import read_query_expectation


def run():
    assert sq.and_(sq.term("blue"), ordered=False).to_json() == read_query_expectation(
        __file__,
        "expected.json",
    )
