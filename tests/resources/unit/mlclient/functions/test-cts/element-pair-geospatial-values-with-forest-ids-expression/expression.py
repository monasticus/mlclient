from mlclient.functions.xqy import cts, fn


def run():
    return cts.element_pair_geospatial_values(
        "item", "latitude", "longitude", forest_ids=fn.count(cts.search().pos(1)),
    ).compile()
