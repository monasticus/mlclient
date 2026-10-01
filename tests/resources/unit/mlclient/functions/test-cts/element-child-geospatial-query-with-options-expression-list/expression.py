from mlclient.functions.xqy import cts, fn


def run():
    return cts.element_child_geospatial_query(
        "item",
        "item",
        cts.box(10, 10, 20, 20),
        options=[fn.string(cts.search().index(1)), fn.string(cts.search().index(2))],
    ).compile()
