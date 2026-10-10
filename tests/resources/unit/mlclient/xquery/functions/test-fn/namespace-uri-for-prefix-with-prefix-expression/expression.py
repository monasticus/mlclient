from mlclient.xquery import cts, fn, xpath


def run():
    return fn.namespace_uri_for_prefix(
        fn.string(cts.search().pos(1)), xpath("/p:item"),
    ).compile(namespaces={"p": "https://example.com/products"})
