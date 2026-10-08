from mlclient.xquery import cts


def run():
    return cts.geospatial_boxes(cts.search().pos(1), longitude_bounds=[2.5]).compile()
