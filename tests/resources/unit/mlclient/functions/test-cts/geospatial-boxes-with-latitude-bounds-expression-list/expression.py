from mlclient.functions.xqy import cts, fn


def run():
    return cts.geospatial_boxes(
        cts.search().pos(1),
        latitude_bounds=[
            fn.count(cts.search().pos(1)),
            fn.count(cts.search().pos(2)),
        ],
    ).compile()
