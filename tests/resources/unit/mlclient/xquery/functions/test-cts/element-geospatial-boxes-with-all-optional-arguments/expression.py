from mlclient.xquery import cts


def run():
    return cts.element_geospatial_boxes(
        "item",
        latitude_bounds=2.5,
        longitude_bounds=2.5,
        options="checked",
        query="needle",
        quality_weight=2.5,
        forest_ids=123,
    ).compile()
