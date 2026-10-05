from mlclient.functions.xqy import cts, fn


def run():
    return cts.element_pair_geospatial_value_match(
        "item",
        "latitude",
        "longitude",
        "prod*",
        forest_ids=fn.count(cts.search().pos(1)),
    ).compile()
