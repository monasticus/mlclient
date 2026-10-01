from mlclient.functions.xqy import cts, fn


def run():
    return cts.element_pair_geospatial_boxes(
        "item",
        "latitude",
        "longitude",
        forest_ids=[fn.count(cts.search().index(1)), fn.count(cts.search().index(2))],
    ).compile()
