from mlclient.xquery import cts


def run():
    return cts.path_geospatial_query("/p:item", cts.box(10, 10, 20, 20)).compile()
