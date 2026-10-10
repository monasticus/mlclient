"""Test DocumentFragmentQuery through the public structured-query API."""

from mlclient.search.structured import DocumentFragmentQuery, TermQuery


def run():
    return DocumentFragmentQuery(TermQuery("blue"))
