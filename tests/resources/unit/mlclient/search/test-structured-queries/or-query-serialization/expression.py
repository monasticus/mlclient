"""Test OrQuery through the public structured-query API."""

from mlclient.search.structured import OrQuery, TermQuery


def run():
    return OrQuery([TermQuery("blue"), TermQuery("green")])
