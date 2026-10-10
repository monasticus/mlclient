"""Test NotQuery through the public structured-query API."""

from mlclient.search.structured import NotQuery, TermQuery


def run():
    return NotQuery(TermQuery("blue"))
