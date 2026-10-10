"""Test ContainerQuery through the public structured-query API."""

from mlclient.search.structured import ContainerQuery, Element, TermQuery


def run():
    return ContainerQuery(
        Element("section", "https://example.com/example"),
        TermQuery("blue"),
        fragment_scope="properties",
    )
