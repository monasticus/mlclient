from mlclient.xquery import cts


def run():
    return cts.json_property_child_geospatial_query(
        "location",
        "point",
        cts.point(10, 20),
        options="coordinate-system=wgs84",
        weight=3,
    )
