"""Test WordQuery through the public structured-query API."""

from mlclient.search.structured import WordQuery


def run():
    return WordQuery([], "blue")
