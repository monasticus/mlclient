"""Structured components reject arguments they cannot serialize when built."""

from mlclient.search.structured import CollectionQuery


def run():
    return CollectionQuery({"a"})
