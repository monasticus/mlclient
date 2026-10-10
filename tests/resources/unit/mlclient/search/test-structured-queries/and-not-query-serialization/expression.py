"""Test AndNotQuery through the public structured-query API."""

from mlclient.search.structured import AndNotQuery, TermQuery


def run():
    return AndNotQuery(TermQuery("blue"), TermQuery("green"))
