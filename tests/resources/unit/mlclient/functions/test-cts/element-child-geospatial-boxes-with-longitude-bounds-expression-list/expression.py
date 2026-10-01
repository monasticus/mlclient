from mlclient.functions.xqy import cts, fn


def run():
    return cts.element_child_geospatial_boxes(
        "item",
        "item",
        longitude_bounds=[
            fn.count(cts.search().index(1)),
            fn.count(cts.search().index(2)),
        ],
    ).compile()
