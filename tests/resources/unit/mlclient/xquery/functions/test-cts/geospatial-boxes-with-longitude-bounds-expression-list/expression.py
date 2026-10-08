from mlclient.xquery import cts, fn


def run():
    return cts.geospatial_boxes(
        cts.search().pos(1),
        longitude_bounds=[
            fn.count(cts.search().pos(1)),
            fn.count(cts.search().pos(2)),
        ],
    ).compile()
