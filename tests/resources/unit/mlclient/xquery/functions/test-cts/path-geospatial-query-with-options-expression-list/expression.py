from mlclient.xquery import cts, fn


def run():
    return cts.path_geospatial_query(
        "/p:item",
        cts.box(10, 10, 20, 20),
        options=[fn.string(cts.search().pos(1)), fn.string(cts.search().pos(2))],
    ).compile()
