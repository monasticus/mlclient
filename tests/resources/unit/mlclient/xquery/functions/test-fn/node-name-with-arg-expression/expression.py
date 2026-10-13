from mlclient.xquery import fn, xpath


def run():
    return fn.node_name(xpath("/p:item")).compile(
        namespaces={"p": "https://example.com/products"},
    )
