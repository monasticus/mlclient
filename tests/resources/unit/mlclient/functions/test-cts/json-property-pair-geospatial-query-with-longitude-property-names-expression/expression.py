from mlclient.functions.xqy import cts, fn


def run():
    return cts.json_property_pair_geospatial_query(
        "price", "price", fn.string(cts.search().index(1)), cts.box(10, 10, 20, 20),
    ).compile()
