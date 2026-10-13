"""Arguments that CTS queries cannot serialize locally are rejected explicitly."""

from mlclient.xquery import cts, fn


def run():
    return cts.element_word_query(fn.node_name(fn.doc("/a.xml")), "blue").serialize()
