from mlclient.xquery import cts


def run():
    return cts.path_geospatial_query(
        "/item/origin",
        cts.point(10, 20),
        options="coordinate-system=wgs84",
        weight=3,
    )
