from mlclient.xquery import cts, fn


def run():
    return cts.element_child_geospatial_values(
        "item", "child-names", options=fn.string(cts.search().pos(1)),
    ).compile()
