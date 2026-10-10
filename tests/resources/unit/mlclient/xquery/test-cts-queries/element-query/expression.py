"""Native ``cts:element-query`` serialization through the public CTS builder."""

from mlclient.xquery import cts, fn

NS = "https://example.com/cts-test"


def run():
    return cts.element_query(["a", fn.qname(NS, "t:b")], cts.word_query("x"))
