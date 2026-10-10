"""Test container-constraint-query serialization."""

from mlclient.search.structured import ContainerConstraintQuery, TrueQuery


def run():
    return ContainerConstraintQuery("section", TrueQuery())
