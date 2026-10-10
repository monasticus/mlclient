"""Test element-constraint-query serialization."""

from mlclient.search.structured import ElementConstraintQuery, TrueQuery


def run():
    return ElementConstraintQuery("section", TrueQuery())
