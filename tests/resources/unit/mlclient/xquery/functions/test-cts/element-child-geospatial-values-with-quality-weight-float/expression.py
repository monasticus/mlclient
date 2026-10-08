from mlclient.xquery import cts


def run():
    return cts.element_child_geospatial_values(
        "item", "child-names", quality_weight=2.5,
    ).compile()
