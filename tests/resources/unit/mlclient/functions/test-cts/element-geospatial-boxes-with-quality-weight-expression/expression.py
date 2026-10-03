from mlclient.functions.xqy import cts, fn


def run():
    return cts.element_geospatial_boxes(
        "item", quality_weight=fn.count(cts.search().pos(1)),
    ).compile()
