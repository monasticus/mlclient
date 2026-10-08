from mlclient.xquery import cts, fn, xpath


def run():
    return fn.resolve_qname(fn.string(cts.search().pos(1)), xpath("/p:item")).compile(
        namespaces={"p": "https://example.com/products"},
    )
