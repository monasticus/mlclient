from mlclient.functions.xqy import cts, fn


def run():
    return cts.element_child_geospatial_value_match(
        "item", "child-names", "prod*", forest_ids=fn.count(cts.search().index(1)),
    ).compile()
