"""Intersection serialization through the public CTS builder."""

from tests.utils.resources import read_query_expectation
from mlclient.xquery import cts


def run():
    assert cts.and_query(["blue"]).serialize() == read_query_expectation(
        __file__,
        "expected-1.json",
    )
