from mlclient.functions.xqy import cts


def run():
    return cts.element_pair_geospatial_query(
        "item", None, "item", cts.box(10, 10, 20, 20),
    ).compile()
