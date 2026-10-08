from mlclient.xquery import cts


def run():
    return cts.element_child_geospatial_value_match(
        "item", "child-names", "prod*",
    ).compile()
