from mlclient.functions.xqy import cts


def run():
    return cts.element_attribute_pair_geospatial_values(
        None, "latitude", "longitude",
    ).compile()
