"""Test AndQuery through the public structured-query API."""

from mlclient.search.structured import AndQuery, TermQuery


def run():
    return AndQuery([TermQuery("blue"), TermQuery("green")], ordered=True)
