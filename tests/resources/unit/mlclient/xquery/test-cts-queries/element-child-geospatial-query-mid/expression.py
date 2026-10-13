from mlclient.xquery import cts


def run():
    return cts.element_child_geospatial_query(
        "location",
        "point",
        cts.point(10, 20),
        weight=3,
    )
