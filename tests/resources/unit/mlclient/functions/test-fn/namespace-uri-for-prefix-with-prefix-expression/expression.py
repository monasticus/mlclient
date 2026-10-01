from mlclient.functions.xqy import cts, fn, xpath


def run():
    return fn.namespace_uri_for_prefix(
        fn.string(cts.search().index(1)), xpath("/p:item"),
    ).compile(namespaces={"p": "https://example.com/products"})
