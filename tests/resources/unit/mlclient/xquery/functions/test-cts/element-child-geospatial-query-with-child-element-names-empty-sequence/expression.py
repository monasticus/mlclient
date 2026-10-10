from mlclient.xquery import cts


def run():
    return cts.element_child_geospatial_query(
        "item", None, cts.box(10, 10, 20, 20),
    ).compile()
