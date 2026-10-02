from mlclient.functions.xqy import cts, fn


def run():
    return cts.path_geospatial_query(
        "/p:item", cts.box(10, 10, 20, 20), weight=fn.count(cts.search().pos(1)),
    ).compile()
