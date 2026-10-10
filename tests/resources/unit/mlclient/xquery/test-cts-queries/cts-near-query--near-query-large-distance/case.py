"""Native proximity query serialization and compilation."""

from tests.utils.resources import read_query_expectation
from mlclient.xquery import cts


def run():
    assert cts.near_query(
        [],
        distance=1000000000000,
    ).serialize() == read_query_expectation(__file__, "expected-1.json")
