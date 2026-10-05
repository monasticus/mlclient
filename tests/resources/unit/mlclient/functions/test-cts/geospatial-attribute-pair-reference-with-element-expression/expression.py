from mlclient.functions.xqy import cts, fn


def run():
    return cts.geospatial_attribute_pair_reference(
        fn.qname("https://example.com/products", "p:item"), "latitude", "longitude",
    ).compile()
