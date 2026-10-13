"""Test collection-constraint-query serialization."""

from mlclient.search.structured import CollectionConstraintQuery


def run():
    return CollectionConstraintQuery("category", ["blue", "green"])
