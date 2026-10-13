from mlclient.xquery import fn, xpath


def run():
    return fn.namespace_uri_for_prefix("p", xpath("/p:item")).compile(
        namespaces={"p": "https://example.com/products"},
    )
