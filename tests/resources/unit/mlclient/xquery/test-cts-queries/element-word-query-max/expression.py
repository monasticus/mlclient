"""Native ``cts:element-word-query`` serialization through the public CTS builder."""

from mlclient.xquery import cts, fn

NS = "https://example.com/cts-test"


def run():
    return cts.element_word_query(
        fn.qname(NS, "title"),
        ["blue", "red"],
        options="case-insensitive",
        weight=2,
    )
