from mlclient.functions.xqy import cts, fn, xpath


def run():
    return fn.document(cts.search().index(1), base_node=xpath("/p:item")).compile(
        namespaces={"p": "https://example.com/products"},
    )
