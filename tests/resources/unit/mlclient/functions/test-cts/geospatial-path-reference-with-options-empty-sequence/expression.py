from mlclient.functions.xqy import cts


def run():
    return cts.geospatial_path_reference("/p:item", options=None).compile()
