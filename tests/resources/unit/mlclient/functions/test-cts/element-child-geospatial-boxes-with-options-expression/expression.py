from mlclient.functions.xqy import cts, fn


def run():
    return cts.element_child_geospatial_boxes(
        "item", "item", options=fn.string(cts.search().pos(1)),
    ).compile()
