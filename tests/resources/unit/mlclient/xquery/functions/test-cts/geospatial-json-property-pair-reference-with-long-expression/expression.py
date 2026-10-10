from mlclient.xquery import cts, fn


def run():
    return cts.geospatial_json_property_pair_reference(
        "price", "latitude", fn.string(cts.search().pos(1)),
    ).compile()
