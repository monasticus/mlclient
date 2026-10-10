from mlclient.xquery import fn, xpath


def run():
    return fn.resolve_qname(None, xpath("/p:item")).compile(
        namespaces={"p": "https://example.com/products"},
    )
