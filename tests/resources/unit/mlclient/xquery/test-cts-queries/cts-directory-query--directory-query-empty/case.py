"""Native directory query serialization and compilation."""

from tests.utils.resources import read_query_expectation
from mlclient.xquery import cts


def run():
    assert cts.directory_query([]).serialize() == read_query_expectation(
        __file__,
        "expected-1.json",
    )
