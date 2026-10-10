from mlclient.xquery import cts


def run():
    return cts.element_pair_geospatial_boxes(
        "item", "latitude", "longitude", latitude_bounds=set(),
    )
