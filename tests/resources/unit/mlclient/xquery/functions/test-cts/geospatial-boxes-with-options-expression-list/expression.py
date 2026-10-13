from mlclient.xquery import cts, fn


def run():
    return cts.geospatial_boxes(
        cts.search().pos(1),
        options=[fn.string(cts.search().pos(1)), fn.string(cts.search().pos(2))],
    ).compile()
