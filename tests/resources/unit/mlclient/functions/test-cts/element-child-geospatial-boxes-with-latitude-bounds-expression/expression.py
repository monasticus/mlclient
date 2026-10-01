from mlclient.functions.xqy import cts, fn


def run():
    return cts.element_child_geospatial_boxes(
        "item", "item", latitude_bounds=fn.count(cts.search().index(1)),
    ).compile()
