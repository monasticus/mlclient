from mlclient.xquery import fn, xpath


def run():
    return fn.idref("arg", node=xpath("/p:item")).compile(
        namespaces={"p": "https://example.com/products"},
    )
