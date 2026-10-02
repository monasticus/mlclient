from mlclient.functions.xqy import cts


def run():
    return cts.geospatial_boxes(cts.search().pos(1), latitude_bounds=2.5).compile()
