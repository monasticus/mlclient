from mlclient.xquery import fn, xpath


def run():
    return fn.nilled(xpath("/p:item")).compile(
        namespaces={"p": "https://example.com/products"},
    )
