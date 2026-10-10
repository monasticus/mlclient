from mlclient.xquery import cts, fn


def run():
    return cts.element_attribute_pair_geospatial_boxes(
        [
            fn.qname("https://example.com/products", "p:item"),
            fn.qname("https://example.com/products", "p:item"),
        ],
        "latitude",
        "longitude",
    ).compile()
