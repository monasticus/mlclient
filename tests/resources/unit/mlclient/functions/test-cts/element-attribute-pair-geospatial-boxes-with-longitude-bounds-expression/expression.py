from mlclient.functions.xqy import cts, fn


def run():
    return cts.element_attribute_pair_geospatial_boxes(
        "item",
        "latitude",
        "longitude",
        longitude_bounds=fn.count(cts.search().index(1)),
    ).compile()
