from mlclient.functions.xqy import cts


def run():
    return cts.element_child_geospatial_boxes(
        "item", "item", quality_weight=2.5,
    ).compile()
