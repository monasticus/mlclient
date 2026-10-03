from mlclient.functions.xqy import cts


def run():
    return cts.element_geospatial_query(None, cts.box(10, 10, 20, 20)).compile()
