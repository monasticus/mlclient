from mlclient.xquery import cts, fn


def run():
    return cts.element_child_geospatial_value_match(
        "item",
        "child-names",
        "prod*",
        forest_ids=[fn.count(cts.search().pos(1)), fn.count(cts.search().pos(2))],
    ).compile()
