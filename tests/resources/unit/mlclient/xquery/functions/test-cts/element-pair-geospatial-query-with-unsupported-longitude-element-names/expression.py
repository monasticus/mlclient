from mlclient.xquery import cts


def run():
    return cts.element_pair_geospatial_query(
        "item", "item", set(), cts.box(10, 10, 20, 20),
    )
