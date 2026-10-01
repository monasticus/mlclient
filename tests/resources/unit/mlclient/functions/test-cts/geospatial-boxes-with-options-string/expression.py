from mlclient.functions.xqy import cts


def run():
    return cts.geospatial_boxes(cts.search().index(1), options="checked").compile()
