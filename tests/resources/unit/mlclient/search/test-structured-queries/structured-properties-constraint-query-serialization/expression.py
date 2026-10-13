"""Test properties-constraint-query serialization."""

from mlclient.search.structured import PropertiesConstraintQuery, TrueQuery


def run():
    return PropertiesConstraintQuery("metadata", TrueQuery())
