from mlclient.functions.xqy import cts, fn


def run():
    return cts.element_attribute_pair_geospatial_value_match(
        "item", "latitude", "longitude", fn.count(cts.search().index(1)),
    ).compile()
