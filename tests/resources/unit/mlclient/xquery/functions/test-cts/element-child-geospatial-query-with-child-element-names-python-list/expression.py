from mlclient.xquery import cts


def run():
    return cts.element_child_geospatial_query(
        "item", ["item"], cts.box(10, 10, 20, 20),
    ).compile()
