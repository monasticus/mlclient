from mlclient.functions.xqy import cts, fn


def run():
    return cts.element_pair_geospatial_boxes(
        "item",
        "latitude",
        "longitude",
        latitude_bounds=[
            fn.count(cts.search().pos(1)),
            fn.count(cts.search().pos(2)),
        ],
    ).compile()
