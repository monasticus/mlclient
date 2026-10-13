from mlclient.xquery import cts, fn


def run():
    return cts.element_pair_geospatial_boxes(
        "item",
        [fn.string(cts.search().pos(1)), fn.string(cts.search().pos(2))],
        "longitude",
    ).compile()
