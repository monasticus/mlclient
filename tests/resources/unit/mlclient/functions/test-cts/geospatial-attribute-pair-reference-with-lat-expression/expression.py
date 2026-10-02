from mlclient.functions.xqy import cts, fn


def run():
    return cts.geospatial_attribute_pair_reference(
        "item", fn.string(cts.search().pos(1)), "longitude",
    ).compile()
