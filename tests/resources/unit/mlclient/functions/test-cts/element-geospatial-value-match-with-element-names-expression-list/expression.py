from mlclient.functions.xqy import cts, fn


def run():
    return cts.element_geospatial_value_match(
        [
            fn.qname("https://example.com/products", "p:item"),
            fn.qname("https://example.com/products", "p:item"),
        ],
        "prod*",
    ).compile()
