from mlclient.functions.xqy import cts, fn


def run():
    return cts.element_pair_geospatial_values(
        "item",
        "latitude",
        [fn.string(cts.search().index(1)), fn.string(cts.search().index(2))],
    ).compile()
