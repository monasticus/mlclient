"""Test TermQuery through the public structured-query API."""

from mlclient.search.structured import TermQuery


def run():
    return TermQuery(
        ["blue", "green"],
        weight=2,
        options=["case-sensitive", "unstemmed"],
    )
