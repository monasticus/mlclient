from mlclient.xquery import fn, xpath


def run():
    return fn.lang("en", node=xpath("/p:item")).compile(
        namespaces={"p": "https://example.com/products"},
    )
