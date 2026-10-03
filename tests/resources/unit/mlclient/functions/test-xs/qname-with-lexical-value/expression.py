from mlclient.functions.xqy import xs


def run():
    return xs.qname("p:item").compile(
        namespaces={"p": "https://example.com/products"},
    )
