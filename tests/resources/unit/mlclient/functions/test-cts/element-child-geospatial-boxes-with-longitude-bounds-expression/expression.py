from mlclient.functions.xqy import cts, fn


def run():
    return cts.element_child_geospatial_boxes(
        "item", "item", longitude_bounds=fn.count(cts.search().pos(1)),
    ).compile()
