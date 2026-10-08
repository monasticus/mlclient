from mlclient.xquery import cts, fn


def run():
    return cts.geospatial_boxes(
        cts.search().pos(1), forest_ids=fn.count(cts.search().pos(1)),
    ).compile()
