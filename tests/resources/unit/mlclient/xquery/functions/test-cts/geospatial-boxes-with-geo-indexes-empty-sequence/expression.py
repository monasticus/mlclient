from mlclient.xquery import cts


def run():
    return cts.geospatial_boxes(None).compile()
