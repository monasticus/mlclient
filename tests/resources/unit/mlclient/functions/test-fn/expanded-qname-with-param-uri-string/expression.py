from mlclient.functions.xqy import fn


def run():
    return fn.expanded_qname("https://example.com/products", "item").compile()
