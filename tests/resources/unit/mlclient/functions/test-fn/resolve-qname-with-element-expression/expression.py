from mlclient.functions.xqy import fn, xpath


def run():
    return fn.resolve_qname("p:item", xpath("/p:item")).compile(
        namespaces={"p": "https://example.com/products"},
    )
