from mlclient.functions.xqy import fn


def run():
    return fn.function_lookup(
        fn.qname("https://example.com/products", "p:item"), object(),
    )
