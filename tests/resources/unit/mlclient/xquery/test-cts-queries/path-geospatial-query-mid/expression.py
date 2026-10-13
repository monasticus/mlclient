from mlclient.xquery import cts


def run():
    return cts.path_geospatial_query("/item/origin", cts.point(10, 20), weight=3)
