from mlclient.functions.xqy import fn, xpath


def run():
    return fn.id("arg", node=xpath("/p:item")).compile(
        namespaces={"p": "https://example.com/products"},
    )
