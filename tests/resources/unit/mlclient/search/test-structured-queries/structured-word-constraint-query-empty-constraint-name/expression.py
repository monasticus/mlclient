"""Test word-constraint-query serialization."""

from mlclient.search.structured import WordConstraintQuery


def run():
    return WordConstraintQuery("", "blue").serialize("xml")
