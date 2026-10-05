from mlclient.functions.xqy import cts, fn


def run():
    return cts.element_pair_geospatial_values(
        "item",
        "latitude",
        [fn.string(cts.search().pos(1)), fn.string(cts.search().pos(2))],
    ).compile()
