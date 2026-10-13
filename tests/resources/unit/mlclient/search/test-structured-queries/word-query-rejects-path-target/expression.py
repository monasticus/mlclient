"""Test WordQuery through the public structured-query API."""

from mlclient.search.structured import PathIndex, WordQuery


def run():
    return WordQuery(PathIndex("/title"), "blue")
