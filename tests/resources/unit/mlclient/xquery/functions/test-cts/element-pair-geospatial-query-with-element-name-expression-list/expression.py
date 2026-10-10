from mlclient.xquery import cts, fn


def run():
    return cts.element_pair_geospatial_query(
        [
            fn.qname("https://example.com/products", "p:item"),
            fn.qname("https://example.com/products", "p:item"),
        ],
        "item",
        "item",
        cts.box(10, 10, 20, 20),
    ).compile()
