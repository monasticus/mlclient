from mlclient.functions.xqy import cts, fn


def run():
    return cts.element_words(
        [
            fn.qname("https://example.com/products", "p:item"),
            fn.qname("https://example.com/products", "p:item"),
        ],
    ).compile()
