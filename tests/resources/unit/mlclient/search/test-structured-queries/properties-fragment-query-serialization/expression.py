"""Test PropertiesFragmentQuery through the public structured-query API."""

from mlclient.search.structured import PropertiesFragmentQuery, TermQuery


def run():
    return PropertiesFragmentQuery(TermQuery("blue"))
