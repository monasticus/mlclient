from mlclient.xquery import cts


def run():
    return cts.element_attribute_pair_geospatial_query(
        "item",
        "lat",
        "lon",
        cts.point(10, 20),
    )
