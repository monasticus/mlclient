from mlclient.xquery import cts, fn


def run():
    return cts.element_child_geospatial_boxes(
        "item", "item", forest_ids=fn.count(cts.search().pos(1)),
    ).compile()
