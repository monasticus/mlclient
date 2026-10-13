from mlclient.xquery import cts, fn


def run():
    return cts.element_attribute_pair_geospatial_boxes(
        "item",
        "latitude",
        "longitude",
        options=[fn.string(cts.search().pos(1)), fn.string(cts.search().pos(2))],
    ).compile()
