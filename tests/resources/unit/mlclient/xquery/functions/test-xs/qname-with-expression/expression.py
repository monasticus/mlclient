from mlclient.xquery import xs


def run():
    return xs.qname(xs.string("p:item")).compile(
        namespaces={"p": "https://example.com/products"},
    )
