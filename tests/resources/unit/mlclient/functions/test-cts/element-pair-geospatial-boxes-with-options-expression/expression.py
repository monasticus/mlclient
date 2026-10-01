from mlclient.functions.xqy import cts, fn


def run():
    return cts.element_pair_geospatial_boxes(
        "item", "latitude", "longitude", options=fn.string(cts.search().index(1)),
    ).compile()
