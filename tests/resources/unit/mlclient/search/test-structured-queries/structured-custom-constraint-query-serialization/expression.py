"""Test custom-constraint-query serialization."""

from mlclient.search.structured import CustomConstraintQuery


def run():
    return CustomConstraintQuery("custom", ["blue", "green"])
