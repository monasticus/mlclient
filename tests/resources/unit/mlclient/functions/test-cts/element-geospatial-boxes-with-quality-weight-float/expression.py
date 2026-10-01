from mlclient.functions.xqy import cts


def run():
    return cts.element_geospatial_boxes("item", quality_weight=2.5).compile()
