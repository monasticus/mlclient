from mlclient.functions.xqy import fn, xpath


def run():
    return fn.document_uri(xpath("/p:item")).compile(
        namespaces={"p": "https://example.com/products"},
    )
