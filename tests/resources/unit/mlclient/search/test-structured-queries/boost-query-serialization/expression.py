"""Test BoostQuery through the public structured-query API."""

from mlclient.search.structured import BoostQuery, TermQuery


def run():
    return BoostQuery(TermQuery("blue"), TermQuery("green", weight=2))
