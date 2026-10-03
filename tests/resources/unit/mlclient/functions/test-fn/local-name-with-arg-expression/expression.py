from mlclient.functions.xqy import fn, xpath


def run():
    return fn.local_name(xpath("/p:item")).compile(
        namespaces={"p": "https://example.com/products"},
    )
