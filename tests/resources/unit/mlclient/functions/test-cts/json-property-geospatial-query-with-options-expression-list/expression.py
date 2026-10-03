from mlclient.functions.xqy import cts, fn


def run():
    return cts.json_property_geospatial_query(
        "price",
        cts.box(10, 10, 20, 20),
        options=[fn.string(cts.search().pos(1)), fn.string(cts.search().pos(2))],
    ).compile()
