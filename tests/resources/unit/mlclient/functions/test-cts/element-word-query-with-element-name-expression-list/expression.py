from mlclient.functions.xqy import cts, fn


def run():
    return cts.element_word_query(
        [
            fn.qname("https://example.com/products", "p:item"),
            fn.qname("https://example.com/products", "p:item"),
        ],
        "MarkLogic search",
    ).compile()
