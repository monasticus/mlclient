"""Test WordQuery through the public structured-query API."""

from mlclient.search.structured import Element, WordQuery


def run():
    return WordQuery(Element("title"), "blue", fragment_scope="locks")
