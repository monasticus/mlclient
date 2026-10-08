from mlclient.xquery import cts


def run():
    return cts.element_pair_geospatial_query(
        "item", "item", "item", cts.box(10, 10, 20, 20), weight=2.5,
    ).compile()
