from mlclient.xquery import fn, xpath


def run():
    return fn.in_scope_prefixes(xpath("/p:item")).compile(
        namespaces={"p": "https://example.com/products"},
    )
