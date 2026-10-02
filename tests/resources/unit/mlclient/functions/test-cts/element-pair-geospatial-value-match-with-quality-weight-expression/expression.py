from mlclient.functions.xqy import cts, fn


def run():
    return cts.element_pair_geospatial_value_match(
        "item",
        "latitude",
        "longitude",
        "prod*",
        quality_weight=fn.count(cts.search().pos(1)),
    ).compile()
