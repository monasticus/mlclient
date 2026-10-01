from mlclient.functions.xqy import cts, fn


def run():
    return cts.geospatial_boxes(
        cts.search().index(1), latitude_bounds=fn.count(cts.search().index(1)),
    ).compile()
