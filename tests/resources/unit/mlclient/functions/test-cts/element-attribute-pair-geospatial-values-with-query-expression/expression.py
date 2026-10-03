from mlclient.functions.xqy import cts


def run():
    return cts.element_attribute_pair_geospatial_values(
        "item", "latitude", "longitude", query=cts.collection_query("products"),
    ).compile()
