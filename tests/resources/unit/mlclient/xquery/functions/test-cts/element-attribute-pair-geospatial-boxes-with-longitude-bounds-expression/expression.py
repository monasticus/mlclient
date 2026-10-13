from mlclient.xquery import cts, fn


def run():
    return cts.element_attribute_pair_geospatial_boxes(
        "item",
        "latitude",
        "longitude",
        longitude_bounds=fn.count(cts.search().pos(1)),
    ).compile()
