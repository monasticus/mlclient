from mlclient.xquery import cts


def run():
    return cts.geospatial_boxes(cts.search().pos(1), quality_weight=2.5).compile()
