"""Native proximity query serialization and compilation."""

from tests.utils.resources import read_query_expectation
from mlclient.xquery import cts


def run():
    assert cts.near_query(
        [],
        options="minimum-distance=4294967296",
    ).serialize() == read_query_expectation(__file__, "expected-1.json")
