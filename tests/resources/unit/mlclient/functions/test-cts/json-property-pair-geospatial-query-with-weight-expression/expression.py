from mlclient.functions.xqy import cts, fn


def run():
    return cts.json_property_pair_geospatial_query(
        "price",
        "price",
        "price",
        cts.box(10, 10, 20, 20),
        weight=fn.count(cts.search().pos(1)),
    ).compile()
