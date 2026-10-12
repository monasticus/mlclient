"""Intersection serialization through the public CTS builder."""

from mlclient.xquery import cts


def run():
    return cts.and_query(
        [cts.word_query("blue", options="lang=en"), cts.collection_query("reports")],
        options="ordered",
    )
