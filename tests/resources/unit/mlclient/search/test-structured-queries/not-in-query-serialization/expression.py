"""Test NotInQuery through the public structured-query API."""

from mlclient.search.structured import NotInQuery, TermQuery


def run():
    return NotInQuery(TermQuery("blue"), TermQuery("green"))
