from mlclient.functions.xqy import cts, fn


def run():
    return cts.geospatial_json_property_pair_reference(
        fn.string(cts.search().index(1)), "latitude", "longitude",
    ).compile()
