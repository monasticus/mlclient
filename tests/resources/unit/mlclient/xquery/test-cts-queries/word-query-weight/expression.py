"""Native word-query serialization through the public CTS builder."""

from mlclient.xquery import cts


def run():
    return cts.word_query("blue", weight=0.5)
