from mlclient.xquery import cts, fn


def run():
    return cts.element_pair_geospatial_value_match(
        fn.qname("https://example.com/products", "p:item"),
        "latitude",
        "longitude",
        "prod*",
    ).compile()
