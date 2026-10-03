from mlclient.functions.xqy import cts, fn


def run():
    return cts.geospatial_attribute_pair_reference(
        "item", "latitude", "longitude", options=fn.string(cts.search().pos(1)),
    ).compile()
