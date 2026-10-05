from mlclient.functions.xqy import cts


def run():
    return cts.element_pair_geospatial_values(
        "item", "latitude", "longitude", forest_ids=set(),
    )
