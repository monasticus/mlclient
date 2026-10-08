from mlclient.xquery import fn, xpath


def run():
    return fn.base_uri(xpath("/p:item")).compile(
        namespaces={"p": "https://example.com/products"},
    )
