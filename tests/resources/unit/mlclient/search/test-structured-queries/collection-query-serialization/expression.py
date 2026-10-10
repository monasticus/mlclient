"""Test CollectionQuery through the public structured-query API."""

from mlclient.search.structured import CollectionQuery


def run():
    return CollectionQuery(["reports", "notes"])
