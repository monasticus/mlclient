from mlclient.functions.xqy import fn, xpath


def run():
    return fn.generate_id(xpath("/p:item")).compile(
        namespaces={"p": "https://example.com/products"},
    )
