from mlclient.xquery import cts, fn


def run():
    return cts.element_attribute_pair_geospatial_values(
        "item",
        "latitude",
        "longitude",
        forest_ids=[fn.count(cts.search().pos(1)), fn.count(cts.search().pos(2))],
    ).compile()
