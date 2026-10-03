from mlclient.functions.xqy import cts, fn


def run():
    return cts.element_child_geospatial_boxes(
        "item",
        "item",
        forest_ids=[fn.count(cts.search().pos(1)), fn.count(cts.search().pos(2))],
    ).compile()
