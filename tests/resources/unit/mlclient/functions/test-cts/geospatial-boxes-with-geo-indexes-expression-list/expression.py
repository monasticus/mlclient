from mlclient.functions.xqy import cts


def run():
    return cts.geospatial_boxes(
        [cts.search().index(1), cts.search().index(2)],
    ).compile()
