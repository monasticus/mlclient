"""Native ``cts:document-root-query`` serialization through the public CTS builder."""

from mlclient.xquery import cts, fn

NS = "https://example.com/cts-test"


def run():
    return cts.document_root_query(fn.qname(NS, "t:root"))
