from mlclient.xquery import cts


def run():
    return cts.json_property_geospatial_query("origin", cts.point(10, 20), weight=3)
