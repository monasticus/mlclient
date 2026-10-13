from mlclient.xquery import cts


def run():
    return cts.json_property_pair_geospatial_query(
        "location",
        "lat",
        "lon",
        cts.point(10, 20),
        options="coordinate-system=wgs84",
        weight=3,
    )
