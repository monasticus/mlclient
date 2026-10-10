from mlclient.xquery import cts, fn


def run():
    return cts.element_geospatial_query(
        "item", cts.box(10, 10, 20, 20), options=fn.string(cts.search().pos(1)),
    ).compile()
