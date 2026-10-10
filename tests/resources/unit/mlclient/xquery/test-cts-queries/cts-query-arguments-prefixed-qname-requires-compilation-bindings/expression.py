"""Arguments that CTS queries cannot serialize locally are rejected explicitly."""

from mlclient.xquery import cts


def run():
    return cts.element_word_query("t:title", "blue").serialize()
