from mlclient.xquery import cts


def run():
    return cts.element_child_geospatial_values(
        "item", "child-names", query=None,
    ).compile()
