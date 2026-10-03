from mlclient.functions.xqy import cts


def run():
    return cts.element_child_geospatial_query(set(), "item", cts.box(10, 10, 20, 20))
