from mlclient.functions.xqy import cts, fn


def run():
    return cts.element_attribute_pair_geospatial_boxes(
        "item", "latitude", "longitude", forest_ids=fn.count(cts.search().pos(1)),
    ).compile()
