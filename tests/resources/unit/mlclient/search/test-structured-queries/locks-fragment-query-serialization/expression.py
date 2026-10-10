"""Test LocksFragmentQuery through the public structured-query API."""

from mlclient.search.structured import LocksFragmentQuery, TermQuery


def run():
    return LocksFragmentQuery(TermQuery("blue"))
