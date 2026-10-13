from mlclient.xquery import fn


def run():
    return fn.expanded_qname("https://example.com/products", object())
