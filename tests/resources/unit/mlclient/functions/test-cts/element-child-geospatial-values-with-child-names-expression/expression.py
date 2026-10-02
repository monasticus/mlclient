from mlclient.functions.xqy import cts, fn


def run():
    return cts.element_child_geospatial_values(
        "item", fn.string(cts.search().pos(1)),
    ).compile()
