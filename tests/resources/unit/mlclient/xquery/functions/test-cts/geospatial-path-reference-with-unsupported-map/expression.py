from mlclient.xquery import cts


def run():
    return cts.geospatial_path_reference("/p:item", map=set())
