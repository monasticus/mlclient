from mlclient.functions.xqy import cts, fn


def run():
    return cts.element_child_geospatial_value_match(
        "item", fn.string(cts.search().index(1)), "prod*",
    ).compile()
