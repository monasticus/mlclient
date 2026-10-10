from mlclient.xquery import cts


def run():
    return cts.element_attribute_pair_geospatial_boxes(
        "item", "latitude", None,
    ).compile()
