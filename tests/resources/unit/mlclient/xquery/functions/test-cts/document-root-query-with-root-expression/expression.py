from mlclient.xquery import cts, fn


def run():
    return cts.document_root_query(
        fn.qname("https://example.com/products", "p:item"),
    ).compile()
