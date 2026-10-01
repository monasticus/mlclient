from mlclient.functions.xqy import cts, fn


def run():
    return cts.element_child_geospatial_values(
        "item", [fn.string(cts.search().index(1)), fn.string(cts.search().index(2))],
    ).compile()
