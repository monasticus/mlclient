from mlclient.functions.xqy import cts


def run():
    return cts.geospatial_boxes(cts.search().index(1), quality_weight=2.5).compile()
