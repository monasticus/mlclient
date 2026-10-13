from mlclient.xquery import xs


def run():
    return xs.qname("p:item").compile(
        namespaces={"p": "https://example.com/products"},
    )
