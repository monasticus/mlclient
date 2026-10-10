from mlclient.xquery import cts


def run():
    return cts.element_attribute_pair_geospatial_boxes(
        "item", "latitude", "longitude", query=cts.collection_query("products"),
    ).compile()
