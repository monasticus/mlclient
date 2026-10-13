"""Test WordQuery through the public structured-query API."""

from mlclient.search.structured import Attribute, Element, WordQuery


def run():
    return WordQuery(
        [Element("title"), Element("label")],
        ["blue", "green"],
        attribute=[Attribute("name"), Attribute("alt")],
        options=["case-sensitive"],
        weight=2,
        fragment_scope="documents",
    )
