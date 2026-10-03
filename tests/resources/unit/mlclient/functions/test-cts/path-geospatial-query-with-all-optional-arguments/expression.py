from mlclient.functions.xqy import cts


def run():
    return cts.path_geospatial_query(
        "/p:item", cts.box(10, 10, 20, 20), options="checked", weight=2.5,
    ).compile()
