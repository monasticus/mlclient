from mlclient.xquery import cts, fn


def run():
    return cts.element_child_geospatial_boxes(
        "item", "item", latitude_bounds=fn.count(cts.search().pos(1)),
    ).compile()
