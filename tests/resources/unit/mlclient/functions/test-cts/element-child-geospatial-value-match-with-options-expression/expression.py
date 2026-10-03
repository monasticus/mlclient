from mlclient.functions.xqy import cts, fn


def run():
    return cts.element_child_geospatial_value_match(
        "item", "child-names", "prod*", options=fn.string(cts.search().pos(1)),
    ).compile()
