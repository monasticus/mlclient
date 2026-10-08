from mlclient.xquery import cts, fn


def run():
    return fn.function_lookup(
        fn.qname("https://example.com/products", "p:item"),
        fn.count(cts.search().pos(1)),
    ).compile()
