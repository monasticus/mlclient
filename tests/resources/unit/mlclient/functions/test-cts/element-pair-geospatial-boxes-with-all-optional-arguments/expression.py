from mlclient.functions.xqy import cts


def run():
    return cts.element_pair_geospatial_boxes(
        "item",
        "latitude",
        "longitude",
        latitude_bounds=2.5,
        longitude_bounds=2.5,
        options="checked",
        query="needle",
        quality_weight=2.5,
        forest_ids=123,
    ).compile()
