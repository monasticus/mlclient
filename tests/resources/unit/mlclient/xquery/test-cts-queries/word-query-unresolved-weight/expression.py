"""Native word-query serialization through the public CTS builder."""

from mlclient.xquery import cts, fn


def run():
    return cts.word_query("blue", weight=fn.last()).serialize()
