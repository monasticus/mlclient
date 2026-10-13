from mlclient.xquery import fn, xpath


def run():
    return fn.name(xpath("/p:item")).compile(
        namespaces={"p": "https://example.com/products"},
    )
