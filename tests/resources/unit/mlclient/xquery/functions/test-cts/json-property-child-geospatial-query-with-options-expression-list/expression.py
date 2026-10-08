from mlclient.xquery import cts, fn


def run():
    return cts.json_property_child_geospatial_query(
        "price",
        "price",
        cts.box(10, 10, 20, 20),
        options=[fn.string(cts.search().pos(1)), fn.string(cts.search().pos(2))],
    ).compile()
