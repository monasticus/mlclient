from mlclient.xquery import fn, xpath


def run():
    return fn.key("product", "42", top=xpath("/p:item")).compile(
        namespaces={"p": "https://example.com/products"},
    )
