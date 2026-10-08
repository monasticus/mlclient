from mlclient.xquery import cts, fn


def run():
    return cts.element_child_geospatial_value_match(
        "item", fn.string(cts.search().pos(1)), "prod*",
    ).compile()
