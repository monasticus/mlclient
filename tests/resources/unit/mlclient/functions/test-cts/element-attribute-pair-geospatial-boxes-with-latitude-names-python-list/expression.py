from mlclient.functions.xqy import cts


def run():
    return cts.element_attribute_pair_geospatial_boxes(
        "item", ["latitude"], "longitude",
    ).compile()
