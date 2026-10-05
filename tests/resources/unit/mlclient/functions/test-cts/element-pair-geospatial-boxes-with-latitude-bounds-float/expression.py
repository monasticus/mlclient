from mlclient.functions.xqy import cts


def run():
    return cts.element_pair_geospatial_boxes(
        "item", "latitude", "longitude", latitude_bounds=2.5,
    ).compile()
