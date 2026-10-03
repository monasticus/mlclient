from mlclient.functions.xqy import cts


def run():
    return cts.element_pair_geospatial_query(
        set(), "item", "item", cts.box(10, 10, 20, 20),
    )
