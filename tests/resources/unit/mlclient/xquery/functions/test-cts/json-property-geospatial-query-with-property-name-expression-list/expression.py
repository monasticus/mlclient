from mlclient.xquery import cts, fn


def run():
    return cts.json_property_geospatial_query(
        [fn.string(cts.search().pos(1)), fn.string(cts.search().pos(2))],
        cts.box(10, 10, 20, 20),
    ).compile()
