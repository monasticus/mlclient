"""Test ContainerQuery through the public structured-query API."""

from mlclient.search.structured import ContainerQuery, Field, TermQuery


def run():
    return ContainerQuery(Field("body"), TermQuery("blue"))
